"""
AirCasta - Settings and Preferences Dialog
Provides comprehensive configuration for image quality, resolution, framerate,
color range, hardware codecs, audio sinks, and network settings.
"""

from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QVBoxLayout
)

from airplay_backend.config import ConfigManager


class SettingsDialog(QDialog):
    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Параметры AirCasta")
        self.setFixedWidth(500)
        self.setModal(True)

        self._init_ui()
        self._load_values()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Image Quality Transmission Settings (Primary)
        quality_group = QGroupBox("Качество передачи изображения")
        quality_layout = QGridLayout(quality_group)
        quality_layout.setContentsMargins(14, 16, 14, 14)
        quality_layout.setSpacing(10)

        # Resolution dropdown
        quality_layout.addWidget(QLabel("Разрешение:"), 0, 0)
        self.res_cb = QComboBox()
        self.res_cb.addItem("1080p Full HD (1920×1080) — Оптимально", "1920x1080")
        self.res_cb.addItem("2K QHD (2560×1440) — Высокая чёткость", "2560x1440")
        self.res_cb.addItem("4K UHD (3840×2160) — Максимальное", "3840x2160")
        self.res_cb.addItem("720p HD (1280×720) — Экономия канала", "1280x720")
        self.res_cb.addItem("Авто (стандартное iOS)", "auto")
        quality_layout.addWidget(self.res_cb, 0, 1)

        # Framerate dropdown
        quality_layout.addWidget(QLabel("Частота кадров:"), 1, 0)
        self.fps_cb = QComboBox()
        self.fps_cb.addItem("60 FPS (Максимальная плавность)", 60)
        self.fps_cb.addItem("30 FPS (Меньше нагрузка на сеть)", 30)
        quality_layout.addWidget(self.fps_cb, 1, 1)

        # Codec & Color Checkboxes
        self.h265_cb = QCheckBox("Кодек H.265 (HEVC) — повышенная чёткость деталей")
        self.h265_cb.setToolTip("Использовать высокоэффективный кодек H.265 для уменьшения артефактов сжатия")
        quality_layout.addWidget(self.h265_cb, 2, 0, 1, 2)

        self.color_cb = QCheckBox("Полный цветовой диапазон (Full Range sRGB 0–255)")
        self.color_cb.setToolTip("Отображение полного динамического диапазона цветов для мониторов ПК")
        quality_layout.addWidget(self.color_cb, 3, 0, 1, 2)

        self.low_latency_cb = QCheckBox("Минимальная задержка без буферизации (-vsync no)")
        self.low_latency_cb.setToolTip("Отключает буферизацию кадров для мгновенного отклика при управлении")
        quality_layout.addWidget(self.low_latency_cb, 4, 0, 1, 2)

        layout.addWidget(quality_group)

        # 2. Rendering & Audio
        av_group = QGroupBox("Видеорендер и Аудио")
        av_layout = QGridLayout(av_group)
        av_layout.setContentsMargins(14, 16, 14, 14)
        av_layout.setSpacing(10)

        av_layout.addWidget(QLabel("Видеорендер:"), 0, 0)
        self.video_sink_cb = QComboBox()
        self.video_sink_cb.addItems([
            "Direct3D 11 (Рекомендуется)",
            "Direct3D 12",
            "Автовыбор",
            "OpenGL"
        ])
        av_layout.addWidget(self.video_sink_cb, 0, 1)

        av_layout.addWidget(QLabel("Аудиовыход:"), 1, 0)
        self.audio_sink_cb = QComboBox()
        self.audio_sink_cb.addItems([
            "WASAPI (Низкая задержка)",
            "DirectSound",
            "Автовыбор",
            "Отключить звук"
        ])
        av_layout.addWidget(self.audio_sink_cb, 1, 1)

        layout.addWidget(av_group)

        # 3. Device Identification & Security
        sec_group = QGroupBox("Устройство и Безопасность")
        sec_layout = QGridLayout(sec_group)
        sec_layout.setContentsMargins(14, 16, 14, 14)
        sec_layout.setSpacing(10)

        sec_layout.addWidget(QLabel("Имя на iPhone:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("AirCasta")
        sec_layout.addWidget(self.name_edit, 0, 1)

        self.require_pin_cb = QCheckBox("Запрашивать PIN-код при подключении")
        self.require_pin_cb.toggled.connect(self._on_pin_toggled)
        sec_layout.addWidget(self.require_pin_cb, 1, 0, 1, 2)

        sec_layout.addWidget(QLabel("Фиксированный PIN:"), 2, 0)
        self.pin_edit = QLineEdit()
        self.pin_edit.setMaxLength(4)
        self.pin_edit.setPlaceholderText("Оставьте пустым для случайного")
        sec_layout.addWidget(self.pin_edit, 2, 1)

        layout.addWidget(sec_group)

        # 4. DropCast File Transfer
        ad_group = QGroupBox("DropCast (Передача файлов)")
        ad_layout = QGridLayout(ad_group)
        ad_layout.setContentsMargins(14, 16, 14, 14)
        ad_layout.setSpacing(10)

        self.airdrop_enabled_cb = QCheckBox("Включить локальный сервис DropCast")
        ad_layout.addWidget(self.airdrop_enabled_cb, 0, 0, 1, 2)

        ad_layout.addWidget(QLabel("Папка для файлов:"), 1, 0)
        path_row = QHBoxLayout()
        self.airdrop_path_edit = QLineEdit()
        path_row.addWidget(self.airdrop_path_edit, 1)
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self._browse_airdrop_path)
        path_row.addWidget(browse_btn)
        ad_layout.addLayout(path_row, 1, 1)

        self.airdrop_sound_cb = QCheckBox("Звуковой сигнал при получении файлов")
        ad_layout.addWidget(self.airdrop_sound_cb, 2, 0, 1, 2)

        ad_layout.addWidget(QLabel("DropCast HTTP порт:"), 3, 0)
        self.airdrop_port_spin = QSpinBox()
        self.airdrop_port_spin.setRange(1024, 65535)
        self.airdrop_port_spin.setValue(7080)
        ad_layout.addWidget(self.airdrop_port_spin, 3, 1)

        layout.addWidget(ad_group)

        # 5. Network Port
        net_group = QGroupBox("Сеть (AirPlay)")
        net_layout = QGridLayout(net_group)
        net_layout.setContentsMargins(14, 16, 14, 14)
        net_layout.setSpacing(10)

        net_layout.addWidget(QLabel("RTSP TCP порт:"), 0, 0)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(7000)
        net_layout.addWidget(self.port_spin, 0, 1)

        layout.addWidget(net_group)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        reset_btn = QPushButton("Сброс")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Сохранить")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setProperty("class", "btn-primary")
        save_btn.clicked.connect(self._save_values)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_pin_toggled(self, checked: bool):
        self.pin_edit.setEnabled(checked)

    def _browse_airdrop_path(self):
        sel = QFileDialog.getExistingDirectory(self, "Папка для сохранения файлов DropCast", self.airdrop_path_edit.text())
        if sel:
            self.airdrop_path_edit.setText(sel)

    def _load_values(self):
        # 1. Quality & Resolution
        cur_res = self.config.get("video_resolution", "1920x1080")
        res_idx = self.res_cb.findData(cur_res)
        if res_idx != -1:
            self.res_cb.setCurrentIndex(res_idx)
        else:
            self.res_cb.setCurrentIndex(0)

        cur_fps = self.config.get("max_fps", 60)
        fps_idx = self.fps_cb.findData(cur_fps)
        if fps_idx != -1:
            self.fps_cb.setCurrentIndex(fps_idx)
        else:
            self.fps_cb.setCurrentIndex(0)

        self.h265_cb.setChecked(self.config.get("h265_support", True))
        self.color_cb.setChecked(self.config.get("full_color_range", True))
        self.low_latency_cb.setChecked(not self.config.get("vsync", False))

        # 2. Rendering & Audio
        vs = self.config.get("video_sink_windows", "d3d11videosink")
        if "d3d11" in vs:
            self.video_sink_cb.setCurrentIndex(0)
        elif "d3d12" in vs:
            self.video_sink_cb.setCurrentIndex(1)
        elif "gl" in vs:
            self.video_sink_cb.setCurrentIndex(3)
        else:
            self.video_sink_cb.setCurrentIndex(2)

        asink = self.config.get("audio_sink_windows", "wasapisink")
        if "wasapi" in asink:
            self.audio_sink_cb.setCurrentIndex(0)
        elif "directsound" in asink:
            self.audio_sink_cb.setCurrentIndex(1)
        elif "fake" in asink:
            self.audio_sink_cb.setCurrentIndex(3)
        else:
            self.audio_sink_cb.setCurrentIndex(2)

        # 3. Identification & Security
        self.name_edit.setText(self.config.get("server_name", "AirCasta"))
        require_pin = self.config.get("require_pin", False)
        self.require_pin_cb.setChecked(require_pin)
        self.pin_edit.setText(self.config.get("fixed_pin", ""))
        self.pin_edit.setEnabled(require_pin)

        # 4. AirDrop
        self.airdrop_enabled_cb.setChecked(self.config.get("airdrop_enabled", True))
        self.airdrop_path_edit.setText(self.config.get("airdrop_save_path", str(Path.home() / "Downloads" / "AirCasta")))
        self.airdrop_sound_cb.setChecked(self.config.get("airdrop_sound_enabled", True))
        self.airdrop_port_spin.setValue(self.config.get("airdrop_port", 7080))

        # 5. Network
        self.port_spin.setValue(self.config.get("tcp_port_base", 7000))

    def _save_values(self):
        # 1. Quality & Resolution
        self.config.set("video_resolution", self.res_cb.currentData())
        self.config.set("max_fps", self.fps_cb.currentData())
        self.config.set("h265_support", self.h265_cb.isChecked())
        self.config.set("full_color_range", self.color_cb.isChecked())
        self.config.set("vsync", not self.low_latency_cb.isChecked())

        # 2. Rendering & Audio
        vs_map = {0: "d3d11videosink", 1: "d3d12videosink", 2: "autovideosink", 3: "glimagesink"}
        self.config.set("video_sink_windows", vs_map.get(self.video_sink_cb.currentIndex(), "d3d11videosink"))

        as_map = {0: "wasapisink", 1: "directsoundsink", 2: "autoaudiosink", 3: "fakesink"}
        self.config.set("audio_sink_windows", as_map.get(self.audio_sink_cb.currentIndex(), "wasapisink"))

        # 3. Identification & Security
        self.config.set("server_name", self.name_edit.text().strip() or "AirCasta")
        self.config.set("require_pin", self.require_pin_cb.isChecked())
        self.config.set("fixed_pin", self.pin_edit.text().strip())

        # 4. AirDrop
        self.config.set("airdrop_enabled", self.airdrop_enabled_cb.isChecked())
        self.config.set("airdrop_save_path", self.airdrop_path_edit.text().strip())
        self.config.set("airdrop_sound_enabled", self.airdrop_sound_cb.isChecked())
        self.config.set("airdrop_port", self.airdrop_port_spin.value())

        # 5. Network
        self.config.set("tcp_port_base", self.port_spin.value())

        self.accept()

    def _reset_defaults(self):
        self.res_cb.setCurrentIndex(0)  # 1080p
        self.fps_cb.setCurrentIndex(0)  # 60 FPS
        self.h265_cb.setChecked(True)
        self.color_cb.setChecked(True)
        self.low_latency_cb.setChecked(True)
        self.video_sink_cb.setCurrentIndex(0)
        self.audio_sink_cb.setCurrentIndex(0)
        self.name_edit.setText("AirCasta")
        self.require_pin_cb.setChecked(False)
        self.pin_edit.clear()
        self.airdrop_enabled_cb.setChecked(True)
        self.airdrop_path_edit.setText(str(Path.home() / "Downloads" / "AirCasta"))
        self.airdrop_sound_cb.setChecked(True)
        self.airdrop_port_spin.setValue(7080)
        self.port_spin.setValue(7000)
