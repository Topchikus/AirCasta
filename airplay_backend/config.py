"""
AirCasta - Configuration and Settings Manager
Handles user preferences, persistence, and default AirPlay Receiver settings.
"""

import json
import os
import platform
import socket
from pathlib import Path


def get_default_device_name() -> str:
    try:
        hostname = socket.gethostname()
        if hostname:
            # Clean hostname
            clean_name = "".join(c for c in hostname if c.isalnum() or c in ("-", "_", " ")).strip()
            return f"AirCasta ({clean_name})"
    except Exception:
        pass
    return "AirCasta Receiver"


def get_config_path() -> Path:
    if platform.system() == "Windows":
        base_dir = Path(os.environ.get("APPDATA", Path.home())) / "AirCasta"
    else:
        base_dir = Path.home() / ".config" / "AirCasta"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "settings.json"


DEFAULT_CONFIG = {
    "server_name": get_default_device_name(),
    "airplay_enabled": True,
    "require_pin": False,
    "fixed_pin": "",
    "audio_enabled": True,
    "audio_volume": 100,  # 0 to 100
    # Image Quality Transmission Settings
    "video_resolution": "1920x1080",  # "1920x1080", "2560x1440", "3840x2160", "1280x720", "auto"
    "max_fps": 60,  # 60 or 30
    "h265_support": True,  # -h265 (HEVC 4K/high efficiency codec)
    "full_color_range": True,  # -srgb (Full 0-255 RGB dynamic color range)
    "low_latency_mode": True,
    "vsync": False,  # False minimizes latency for screen mirroring (-vsync no)
    "client_fps_data": True,  # -FPSdata
    "video_sink_windows": "d3d11videosink",  # d3d11videosink or d3d12videosink
    "video_sink_macos": "autovideosink",
    "audio_sink_windows": "wasapisink",
    "audio_sink_macos": "autoaudiosink",
    # AirDrop Transfer Settings
    "airdrop_enabled": True,
    "airdrop_port": 7080,
    "airdrop_save_path": str(Path.home() / "Downloads" / "AirCasta"),
    "airdrop_sound_enabled": True,
    "fullscreen_on_connect": False,
    "tcp_port_base": 7000,
    "udp_port_base": 6000,
    "last_connected_device": ""
}


class ConfigManager:
    def __init__(self, config_file: Path | None = None):
        self.config_file = config_file or get_config_path()
        self.data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"[Config] Error loading config: {e}. Using defaults.")

    def save(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Error saving config: {e}")

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value):
        self.data[key] = value
        self.save()
