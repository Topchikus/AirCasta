"""
AirCasta - Minimalist Video Canvas and Idle State
A distraction-free, professional video viewport with subtle overlay controls.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSlider,
    QVBoxLayout, QWidget, QSizePolicy
)

from airplay_backend.engine import ClientSessionInfo, EngineState


class VideoDisplayWidget(QFrame):
    fullscreen_requested = pyqtSignal()
    volume_changed = pyqtSignal(int)
    mute_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoWidget")
        self.setProperty("class", "canvas-frame")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.is_muted = False
        self.current_fps = 0.0
        self.current_latency = 0.0
        self.device_name = "AirCasta"

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Main Canvas Area (Center)
        self.canvas = QFrame()
        self.canvas.setProperty("class", "canvas-frame")
        canvas_layout = QVBoxLayout(self.canvas)
        canvas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas_layout.setContentsMargins(32, 32, 32, 32)
        canvas_layout.setSpacing(12)

        # Subtle AirPlay Icon (Clean geometric symbol)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 36px; color: #52525b;")
        self.icon_label.setText("⎚")
        canvas_layout.addWidget(self.icon_label)

        # Idle Title
        self.state_title = QLabel("Готов к подключению")
        self.state_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #f4f4f5; letter-spacing: -0.2px;")
        canvas_layout.addWidget(self.state_title)

        # Idle Subtitle / Action hint
        self.state_desc = QLabel("Откройте Пункт управления на iPhone → Повтор экрана")
        self.state_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_desc.setProperty("class", "secondary-label")
        self.state_desc.setWordWrap(True)
        canvas_layout.addWidget(self.state_desc)

        # PIN display card (hidden by default)
        self.pin_box = QFrame()
        self.pin_box.setStyleSheet("""
            QFrame {
                background-color: #141518;
                border: 1px solid #27272a;
                border-radius: 8px;
                padding: 10px 20px;
            }
        """)
        pin_layout = QVBoxLayout(self.pin_box)
        pin_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_layout.setSpacing(6)

        pin_hint = QLabel("Код подтверждения AirPlay")
        pin_hint.setProperty("class", "subtle-label")
        pin_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_layout.addWidget(pin_hint)

        self.pin_code_label = QLabel("----")
        self.pin_code_label.setProperty("class", "pin-code")
        self.pin_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_layout.addWidget(self.pin_code_label)

        self.pin_box.setVisible(False)
        canvas_layout.addWidget(self.pin_box)

        main_layout.addWidget(self.canvas, 1)

        # 2. Sleek Bottom Control Bar
        self.bottom_bar = QFrame()
        self.bottom_bar.setProperty("class", "bottom-panel")
        self.bottom_bar.setFixedHeight(44)
        bar_layout = QHBoxLayout(self.bottom_bar)
        bar_layout.setContentsMargins(16, 0, 16, 0)
        bar_layout.setSpacing(12)

        # Audio mute & volume
        self.mute_btn = QPushButton("Звук")
        self.mute_btn.setProperty("class", "btn-subtle")
        self.mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mute_btn.clicked.connect(self._toggle_mute)
        bar_layout.addWidget(self.mute_btn)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(100)
        self.vol_slider.setFixedWidth(90)
        self.vol_slider.valueChanged.connect(self._on_volume_changed)
        bar_layout.addWidget(self.vol_slider)

        self.vol_label = QLabel("100%")
        self.vol_label.setProperty("class", "subtle-label")
        self.vol_label.setFixedWidth(32)
        bar_layout.addWidget(self.vol_label)

        bar_layout.addStretch()

        # Quality Preset Badge
        self.quality_badge = QLabel("1080p  ·  60 FPS")
        self.quality_badge.setProperty("class", "subtle-label")
        self.quality_badge.setStyleSheet("padding: 3px 8px; background-color: #18191d; border: 1px solid #27272a; border-radius: 4px; font-weight: 500;")
        bar_layout.addWidget(self.quality_badge)

        # Telemetry stats (clean, unobtrusive)
        self.telemetry_label = QLabel("")
        self.telemetry_label.setProperty("class", "subtle-label")
        bar_layout.addWidget(self.telemetry_label)

        bar_layout.addStretch()

        # Fullscreen Button
        self.fs_btn = QPushButton("Полный экран")
        self.fs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fs_btn.clicked.connect(self.fullscreen_requested.emit)
        bar_layout.addWidget(self.fs_btn)

        main_layout.addWidget(self.bottom_bar)

    def set_device_name(self, name: str):
        self.device_name = name

    def set_quality_info(self, res: str, fps: int, h265: bool = True):
        res_display = {
            "1920x1080": "1080p",
            "2560x1440": "2K QHD",
            "3840x2160": "4K UHD",
            "1280x720": "720p",
            "auto": "Авто"
        }.get(res, res)
        text = f"{res_display}  ·  {fps} FPS"
        if h265:
            text += "  ·  H.265"
        self.quality_badge.setText(text)

    def _toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.mute_btn.setText("Без звука")
            self.mute_btn.setStyleSheet("color: #ef4444;")
            self.vol_slider.setEnabled(False)
        else:
            self.mute_btn.setText("Звук")
            self.mute_btn.setStyleSheet("")
            self.vol_slider.setEnabled(True)
        self.mute_toggled.emit(self.is_muted)

    def _on_volume_changed(self, val: int):
        self.vol_label.setText(f"{val}%")
        self.volume_changed.emit(val)

    def show_pin(self, pin: str):
        if pin:
            self.pin_code_label.setText(pin)
            self.pin_box.setVisible(True)
        else:
            self.pin_box.setVisible(False)

    def set_stream_state(self, state: EngineState, info: ClientSessionInfo | None = None):
        if state == EngineState.STREAMING:
            self.icon_label.setText("⎚")
            self.icon_label.setStyleSheet("font-size: 36px; color: #10b981;")
            client_name = info.client_name if info else "iPhone"
            self.state_title.setText(f"Трансляция активна — {client_name}")
            self.state_desc.setText("Окно видеопотока открыто через аппаратный Direct3D рендерер")
            self.pin_box.setVisible(False)
        elif state == EngineState.CONNECTING:
            self.icon_label.setText("⎚")
            self.icon_label.setStyleSheet("font-size: 36px; color: #f59e0b;")
            self.state_title.setText("Подключение...")
            self.state_desc.setText("Установление защищённого сеанса AirPlay")
        elif state == EngineState.STOPPED:
            self.icon_label.setText("⎚")
            self.icon_label.setStyleSheet("font-size: 36px; color: #52525b;")
            self.state_title.setText("Приёмник выключен")
            self.state_desc.setText("Нажмите «Запустить» в верхней панели")
            self.telemetry_label.setText("")
            self.pin_box.setVisible(False)
        else:
            # BROADCASTING
            self.icon_label.setText("⎚")
            self.icon_label.setStyleSheet("font-size: 36px; color: #71717a;")
            self.state_title.setText("Готов к подключению")
            self.state_desc.setText(f"В Пункте управления на iPhone выберите «{self.device_name}»")
            self.telemetry_label.setText("")
            self.pin_box.setVisible(False)

    def update_telemetry(self, fps: float, latency_ms: float):
        self.current_fps = fps
        self.current_latency = latency_ms
        self.telemetry_label.setText(f"{fps:.0f} FPS  ·  {latency_ms:.0f} ms")
