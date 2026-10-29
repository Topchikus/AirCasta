"""
AirCasta - Native AirPlay Engine Manager
Supervises the native AirPlay mirroring backend process, parses protocol events,
telemetry, client connection lifecycle, and PIN challenges.
Includes automatic LAN physical interface routing and dual-layer mDNS broadcasting.
"""

import os
import platform
import re
import shutil
import socket
import subprocess
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

import psutil
from PyQt6.QtCore import QObject, pyqtSignal

from .config import ConfigManager


class EngineState(Enum):
    STOPPED = "Остановлен"
    STARTING = "Запуск приёмника..."
    BROADCASTING = "Ожидание подключения iPhone"
    CONNECTING = "Подключение iPhone..."
    STREAMING = "Трансляция активна"
    DISCONNECTED = "iPhone отключился"
    ERROR = "Ошибка работы"


@dataclass
class ClientSessionInfo:
    client_name: str = "iPhone"
    client_model: str = "iOS Device"
    client_ip: str = ""
    user_agent: str = ""
    resolution: str = "1080x1920"
    fps: float = 0.0
    latency_ms: float = 0.0
    pin_code: str = ""
    audio_active: bool = False


def get_physical_lan_info() -> Tuple[str, str, str]:
    """
    Detects the real physical LAN/Wi-Fi IPv4 address and MAC,
    avoiding VPNs, Radmin, VirtualBox, Clash tunnels, WSL, etc.
    """
    try:
        addrs = psutil.net_if_addrs()
        candidates = []
        for iface_name, iface_addrs in addrs.items():
            name_lower = iface_name.lower()
            if any(bad in name_lower for bad in ("vpn", "radmin", "virtual", "vbox", "wsl", "wwan", "teredo", "tunnel", "loopback")):
                continue

            ip, mac = None, None
            for addr in iface_addrs:
                if addr.family == psutil.AF_LINK and not mac:
                    mac = addr.address.replace("-", ":").lower()
                elif addr.family == socket.AF_INET and not ip:
                    ip_str = addr.address
                    if not ip_str.startswith(("127.", "169.254.", "198.18.")):
                        ip = ip_str

            if ip and mac:
                # Prefer standard private subnets
                score = 10 if ip.startswith("192.168.") else (5 if ip.startswith("10.") else 1)
                candidates.append((score, ip, mac, iface_name))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            _, ip, mac, name = candidates[0]
            return ip, mac, name
    except Exception as e:
        print(f"[Engine] Interface detection error: {e}")

    # Fallback default
    return "192.168.1.201", "9c:6b:00:5e:9d:f8", "Ethernet"


class AirPlayEngine(QObject):
    state_changed = pyqtSignal(object)  # EngineState
    client_connected = pyqtSignal(object)  # ClientSessionInfo
    client_disconnected = pyqtSignal()
    pin_requested = pyqtSignal(str)  # 4-digit PIN
    telemetry_updated = pyqtSignal(float, float)  # fps, latency_ms
    log_received = pyqtSignal(str)

    def __init__(self, config: ConfigManager, binary_path: Optional[Path] = None):
        super().__init__()
        self.config = config
        self.binary_path = binary_path or self.locate_binary()
        self.process: Optional[subprocess.Popen] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.state = EngineState.STOPPED
        self.client_info = ClientSessionInfo()
        self._stop_requested = False

        self.lan_ip, self.lan_mac, self.lan_iface = get_physical_lan_info()

    def locate_binary(self) -> Optional[Path]:
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent
        else:
            base_dir = Path(__file__).resolve().parent.parent

        local_bin = base_dir / "bin" / ("uxplay.exe" if platform.system() == "Windows" else "uxplay")
        if local_bin.exists():
            return local_bin

        if platform.system() == "Windows":
            candidates = [
                Path(r"C:\msys64\ucrt64\bin\uxplay.exe"),
                Path(r"C:\msys64\mingw64\bin\uxplay.exe"),
                Path(r"C:\msys64\usr\bin\uxplay.exe"),
                Path(os.environ.get("LOCALAPPDATA", "")) / "AirCasta" / "uxplay.exe",
            ]
            for candidate in candidates:
                if candidate.exists():
                    return candidate

        system_bin = shutil.which("uxplay")
        if system_bin:
            return Path(system_bin)

        return None

    def is_available(self) -> bool:
        bin_path = self.binary_path or self.locate_binary()
        return bin_path is not None and bin_path.exists()

    def build_command_args(self) -> list[str]:
        if not self.binary_path:
            raise FileNotFoundError("Исполняемый файл AirPlay приёмника не найден.")

        server_name = self.config.get("server_name", "AirCasta")
        args = [str(self.binary_path), "-n", server_name]

        # Bind to physical MAC address to guarantee correct device id in mDNS
        if self.lan_mac:
            args.extend(["-m", self.lan_mac])

        # Image Quality Transmission Settings
        res = self.config.get("video_resolution", "1920x1080")
        max_fps = self.config.get("max_fps", 60)

        # Resolution & refresh rate request to iPhone (-s wxh[@r])
        if res and res != "auto":
            args.extend(["-s", f"{res}@{max_fps}"])
        elif max_fps:
            args.extend(["-fps", str(max_fps)])

        # H.265 / HEVC support
        if self.config.get("h265_support", True):
            args.append("-h265")

        # Full Dynamic RGB Color Range [0-255] for PC monitors
        if self.config.get("full_color_range", True):
            args.append("-srgb")

        # Performance telemetry reporting from client
        if self.config.get("client_fps_data", True):
            args.append("-FPSdata")

        # Low latency video sync
        if not self.config.get("vsync", False):
            args.extend(["-vsync", "no"])

        # Hardware video sink
        if platform.system() == "Windows":
            vs = self.config.get("video_sink_windows", "d3d11videosink")
            args.extend(["-vs", vs])
            asink = self.config.get("audio_sink_windows", "wasapisink")
            if self.config.get("audio_enabled", True):
                args.extend(["-as", asink])
            else:
                args.extend(["-as", "fakesink"])
        else:
            vs = self.config.get("video_sink_macos", "autovideosink")
            args.extend(["-vs", vs])
            asink = self.config.get("audio_sink_macos", "autoaudiosink")
            if self.config.get("audio_enabled", True):
                args.extend(["-as", asink])
            else:
                args.extend(["-as", "fakesink"])

        # PIN authentication
        if self.config.get("require_pin", False):
            fixed_pin = self.config.get("fixed_pin", "").strip()
            if fixed_pin:
                args.extend(["-pw", fixed_pin])
            else:
                args.append("-pin")

        # Port configuration
        port = self.config.get("tcp_port_base", 7000)
        if port != 7000:
            args.extend(["-p", str(port)])

        # Persistent pairing key file
        key_dir = Path(os.environ.get("APPDATA", Path.home())) / "AirCasta"
        key_dir.mkdir(parents=True, exist_ok=True)
        key_path = key_dir / "airplay.pem"
        args.extend(["-key", str(key_path)])

        return args

    @staticmethod
    def _kill_orphaned_instances():
        try:
            current_pid = os.getpid()
            for proc in psutil.process_iter(["name", "pid"]):
                try:
                    name = proc.info.get("name") or ""
                    pid = proc.info.get("pid")
                    if pid != current_pid and "uxplay" in name.lower():
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass

    def start(self):
        # Ensure no zombie backend process is holding ports
        self._kill_orphaned_instances()

        if self.process and self.process.poll() is None:
            return

        self.binary_path = self.locate_binary()
        if not self.binary_path or not self.binary_path.exists():
            self._set_state(EngineState.ERROR)
            self.log_received.emit("ОШИБКА: Исполняемый файл приёмника не найден.")
            return

        # Refresh physical LAN IP and MAC
        self.lan_ip, self.lan_mac, self.lan_iface = get_physical_lan_info()

        try:
            cmd = self.build_command_args()
            self._set_state(EngineState.STARTING)
            print(f"[AirCasta] Сетевой интерфейс: {self.lan_iface} ({self.lan_ip})", flush=True)
            print(f"[AirCasta] Запуск: {' '.join(cmd)}", flush=True)
            self.log_received.emit(f"Интерфейс: {self.lan_iface} ({self.lan_ip})")
            self.log_received.emit(f"Запуск AirPlay: {' '.join(cmd)}")

            env = os.environ.copy()
            # Force UxPlay internal mDNS to use physical LAN IP
            env["AIRCASTA_IP"] = self.lan_ip

            # Add runtime DLLs and GStreamer plugins
            if platform.system() == "Windows":
                if getattr(sys, "frozen", False):
                    project_root = Path(sys.executable).resolve().parent
                else:
                    project_root = Path(__file__).resolve().parent.parent

                local_runtime_bin = project_root / "bin" / "runtime" / "bin"
                local_plugins = project_root / "bin" / "runtime" / "lib" / "gstreamer-1.0"

                if local_runtime_bin.exists():
                    env["PATH"] = f"{local_runtime_bin};" + env.get("PATH", "")
                    env["GST_PLUGIN_PATH"] = str(local_plugins)
                    env["GST_PLUGIN_SYSTEM_PATH"] = str(local_plugins)
                else:
                    ucrt_bin = r"C:\msys64\ucrt64\bin"
                    if os.path.exists(ucrt_bin) and ucrt_bin not in env.get("PATH", ""):
                        env["PATH"] = f"{ucrt_bin};" + env.get("PATH", "")

            # Launch process with pipes.
            # Do NOT use SW_HIDE or CREATE_NO_WINDOW as they hide the GStreamer Direct3D video window!
            self._stop_requested = False
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )

            self.client_info = ClientSessionInfo()
            self.monitor_thread = threading.Thread(target=self._read_output, daemon=True)
            self.monitor_thread.start()
            self._set_state(EngineState.BROADCASTING)

        except Exception as e:
            self._set_state(EngineState.ERROR)
            self.log_received.emit(f"Ошибка при запуске процесса: {e}")

    def stop(self):
        self._stop_requested = True

        if self.process and self.process.poll() is None:
            self.log_received.emit("Остановка приёмника...")
            try:
                self.process.terminate()
                self.process.wait(timeout=2.0)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        self.process = None
        self._set_state(EngineState.STOPPED)

    def _set_state(self, state: EngineState):
        self.state = state
        self.state_changed.emit(state)

    def _read_output(self):
        fps_pattern = re.compile(r"raop_rtp video:.*?latency\s*=\s*([\d\.\-]+).*?size:\s*(\d+)", re.IGNORECASE)
        pin_pattern = re.compile(r"PIN\s*=\s*\"?(\d{4})\"?", re.IGNORECASE)
        user_agent_pattern = re.compile(r"User-Agent:\s*(.*)", re.IGNORECASE)
        client_ip_pattern = re.compile(r"Accepted connection from\s*([0-9a-fA-F\.\:]+)", re.IGNORECASE)

        if not self.process or not self.process.stdout:
            return

        for raw_line in iter(self.process.stdout.readline, ""):
            line = raw_line.strip()
            if not line:
                continue

            # Output to console for live diagnostics in run.bat terminal
            print(f"[AirCasta] {line}", flush=True)

            self.log_received.emit(line)

            # 1. Check for PIN challenges
            pin_match = pin_pattern.search(line)
            if pin_match:
                pin = pin_match.group(1)
                self.client_info.pin_code = pin
                self.pin_requested.emit(pin)

            # 2. Check for Client IP
            ip_match = client_ip_pattern.search(line)
            if ip_match:
                self.client_info.client_ip = ip_match.group(1)
                self._set_state(EngineState.CONNECTING)

            # 3. Check for User-Agent
            ua_match = user_agent_pattern.search(line)
            if ua_match:
                self.client_info.user_agent = ua_match.group(1)
                if "iPhone" in line:
                    self.client_info.client_model = "iPhone"
                elif "iPad" in line:
                    self.client_info.client_model = "iPad"
                elif "Mac" in line:
                    self.client_info.client_model = "Mac"

            # 4. Check for Mirroring activation
            if any(k in line.lower() for k in ("mirroring initialized", "playing video", "video_process", "video_renderer_start", "raop_rtp video")):
                if self.state != EngineState.STREAMING:
                    self._set_state(EngineState.STREAMING)
                    self.client_connected.emit(self.client_info)

            # 5. Check for Video Telemetry
            tele_match = fps_pattern.search(line)
            if tele_match:
                try:
                    latency = float(tele_match.group(1)) * 1000.0
                    self.client_info.latency_ms = max(0.0, latency)
                    self.telemetry_updated.emit(self.client_info.fps or 60.0, self.client_info.latency_ms)
                except Exception:
                    pass

            # 6. Check for Disconnection
            if "TEARDOWN" in line or "client disconnected" in line.lower() or "connection closed" in line.lower():
                self._set_state(EngineState.DISCONNECTED)
                self.client_disconnected.emit()
                self._set_state(EngineState.BROADCASTING)

        if not self._stop_requested:
            self._set_state(EngineState.STOPPED)
            self.log_received.emit("Процесс приёмника завершил работу.")
