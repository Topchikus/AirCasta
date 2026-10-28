"""
AirCasta - DropCast HTTP Server & Streaming Engine
Provides ultra-fast local Wi-Fi file transfer between iPhone and PC without any iOS apps.
Runs asynchronously in a background thread with zero memory overhead.
"""

import asyncio
import os
import platform
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from aiohttp import web
from PyQt6.QtCore import QObject, pyqtSignal

from .html_template import AIRDROP_HTML_TEMPLATE

# Windows notification sound
if platform.system() == "Windows":
    try:
        import winsound
    except ImportError:
        winsound = None
else:
    winsound = None


@dataclass
class TransferredFile:
    id: str
    name: str
    path: str
    size: int
    timestamp: float = field(default_factory=time.time)
    direction: str = "incoming"  # "incoming" (iPhone -> PC) or "outgoing" (PC -> iPhone)
    speed_mbps: float = 0.0


def get_unique_path(directory: Path, filename: str) -> Path:
    """Generates unique file path by appending (1), (2), etc. if file exists."""
    target = directory / filename
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        candidate = directory / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


class DropCastServer(QObject):
    file_received = pyqtSignal(object)  # TransferredFile
    clipboard_received = pyqtSignal(str)
    status_changed = pyqtSignal(bool, str)  # is_running, url

    def __init__(self, lan_ip: str, port: int = 7080, save_path: Optional[str] = None, pc_name: str = "AirCasta PC"):
        super().__init__()
        self.lan_ip = lan_ip
        self.port = port
        self.pc_name = pc_name
        self.save_directory = Path(save_path or (Path.home() / "Downloads" / "AirCasta"))
        self.save_directory.mkdir(parents=True, exist_ok=True)

        self.shared_files: Dict[str, TransferredFile] = {}
        self.received_files: List[TransferredFile] = []
        self.current_clipboard_text = ""

        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner: Optional[web.AppRunner] = None
        self.sound_enabled = True

    @property
    def url(self) -> str:
        return f"http://{self.lan_ip}:{self.port}"

    def set_pc_name(self, name: str):
        self.pc_name = name

    def set_save_directory(self, path: str):
        self.save_directory = Path(path)
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def add_shared_file(self, file_path: str) -> Optional[TransferredFile]:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return None

        file_id = str(uuid.uuid4())[:8]
        tf = TransferredFile(
            id=file_id,
            name=p.name,
            path=str(p.resolve()),
            size=p.stat().st_size,
            direction="outgoing"
        )
        self.shared_files[file_id] = tf
        return tf

    def remove_shared_file(self, file_id: str):
        if file_id in self.shared_files:
            del self.shared_files[file_id]

    def clear_shared_files(self):
        self.shared_files.clear()

    def set_clipboard_text(self, text: str):
        self.current_clipboard_text = text

    def start(self):
        if self._is_running:
            return

        self._is_running = True
        self._thread = threading.Thread(target=self._run_server, daemon=True, name="DropCastServerThread")
        self._thread.start()

    def stop(self):
        if not self._is_running:
            return

        self._is_running = False
        if self._loop and self._runner:
            asyncio.run_coroutine_threadsafe(self._cleanup(), self._loop)

        self.status_changed.emit(False, "")

    def _run_server(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        app = web.Application(client_max_size=10 * 1024 * 1024 * 1024)  # 10 GB max upload
        app.router.add_get("/", self._handle_index)
        app.router.add_post("/api/upload", self._handle_upload)
        app.router.add_get("/api/downloads", self._handle_get_downloads)
        app.router.add_get("/api/download/{id}", self._handle_download_file)
        app.router.add_get("/api/clipboard", self._handle_get_clipboard)
        app.router.add_post("/api/clipboard", self._handle_post_clipboard)

        self._runner = web.AppRunner(app)
        self._loop.run_until_complete(self._runner.setup())

        # Bind to 0.0.0.0 on self.port, fallback to next ports if busy
        actual_port = self.port
        site = None
        for attempt in range(5):
            try:
                site = web.TCPSite(self._runner, "0.0.0.0", actual_port)
                self._loop.run_until_complete(site.start())
                self.port = actual_port
                break
            except Exception:
                actual_port += 1

        if not site:
            print(f"[DropCast] Failed to bind to ports starting at {self.port}")
            self._is_running = False
            self.status_changed.emit(False, "")
            return

        print(f"[DropCast] DropCast server running at {self.url} (saving to {self.save_directory})")
        self.status_changed.emit(True, self.url)

        try:
            self._loop.run_forever()
        except Exception:
            pass
        finally:
            self._loop.run_until_complete(self._cleanup())
            self._loop.close()

    async def _cleanup(self):
        if self._runner:
            await self._runner.cleanup()

    async def _handle_index(self, request: web.Request) -> web.Response:
        html = AIRDROP_HTML_TEMPLATE.replace("__PC_NAME__", self.pc_name)
        return web.Response(text=html, content_type="text/html")

    async def _handle_upload(self, request: web.Request) -> web.Response:
        if not request.can_read_body:
            return web.json_response({"error": "No body"}, status=400)

        reader = await request.multipart()
        saved_items = []
        start_time = time.time()

        while True:
            part = await reader.next()
            if part is None:
                break

            if part.filename:
                # Sanitize filename
                raw_filename = Path(part.filename).name or f"upload_{int(time.time())}.dat"
                target_path = get_unique_path(self.save_directory, raw_filename)

                size = 0
                with open(target_path, "wb") as f:
                    while True:
                        chunk = await part.read_chunk(256 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        size += len(chunk)

                duration = max(0.05, time.time() - start_time)
                speed_mbps = (size / (1024 * 1024)) / duration

                tf = TransferredFile(
                    id=str(uuid.uuid4())[:8],
                    name=target_path.name,
                    path=str(target_path.resolve()),
                    size=size,
                    direction="incoming",
                    speed_mbps=speed_mbps
                )
                self.received_files.insert(0, tf)
                saved_items.append(tf)

                # Play chime sound on Windows
                if self.sound_enabled and winsound:
                    try:
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)
                    except Exception:
                        pass

                # Emit Qt signal on main thread
                self.file_received.emit(tf)

        return web.json_response({
            "status": "ok",
            "count": len(saved_items),
            "files": [{"name": f.name, "size": f.size} for f in saved_items]
        })

    async def _handle_get_downloads(self, request: web.Request) -> web.Response:
        items = [
            {"id": f.id, "name": f.name, "size": f.size}
            for f in self.shared_files.values()
            if Path(f.path).exists()
        ]
        return web.json_response(items)

    async def _handle_download_file(self, request: web.Request) -> web.StreamResponse:
        file_id = request.match_info.get("id", "")
        tf = self.shared_files.get(file_id)
        if not tf or not Path(tf.path).exists():
            return web.Response(status=404, text="Файл не найден")

        return web.FileResponse(
            path=tf.path,
            headers={
                "Content-Disposition": f'attachment; filename="{tf.name}"'
            }
        )

    async def _handle_get_clipboard(self, request: web.Request) -> web.Response:
        return web.json_response({"text": self.current_clipboard_text})

    async def _handle_post_clipboard(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
            text = data.get("text", "").strip()
            if text:
                self.current_clipboard_text = text
                self.clipboard_received.emit(text)
            return web.json_response({"status": "ok"})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)


# Alias for backward compatibility
AirDropServer = DropCastServer
