"""
AirCasta - Minimalist Main Application Window
Coordinates user interface, backend engine lifecycle, settings, and diagnostics.
"""

from pathlib import Path
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget
)

from airdrop_backend.server import DropCastServer, TransferredFile
from airplay_backend.config import ConfigManager
from airplay_backend.engine import AirPlayEngine, ClientSessionInfo, EngineState
from .airdrop_widget import DropCastWidget
from .diag_dialog import DiagnosticsDialog
from .settings_dialog import SettingsDialog
from .video_widget import VideoDisplayWidget


class MainWindow(QMainWindow):
    def __init__(self, config: ConfigManager, engine: AirPlayEngine):
        super().__init__()
        self.config = config
        self.engine = engine

        self.setWindowTitle("AirCasta")
        self.resize(880, 580)
        self.setMinimumSize(700, 460)

        # Initialize DropCast HTTP Server
        airdrop_port = self.config.get("airdrop_port", 7080)
        save_path = self.config.get("airdrop_save_path", str(Path.home() / "Downloads" / "AirCasta"))
        self.airdrop_server = DropCastServer(
            lan_ip=self.engine.lan_ip,
            port=airdrop_port,
            save_path=save_path,
            pc_name=self.config.get("server_name", "AirCasta (Topchikuss)")
        )
        self.airdrop_server.sound_enabled = self.config.get("airdrop_sound_enabled", True)
        if self.config.get("airdrop_enabled", True):
            self.airdrop_server.start()

        self._init_ui()
        self._connect_signals()

        # Synchronize UI with initial engine state
        self._on_engine_state_changed(self.engine.state)

        # Always auto-start receiver on launch
        self.config.set("airplay_enabled", True)
        QTimer.singleShot(150, self._auto_start_engine)

    def _init_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Clean Top Header
        header = QFrame()
        header.setProperty("class", "header-panel")
        header.setFixedHeight(48)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 0, 18, 0)
        header_layout.setSpacing(14)

        # Status Dot (Green / Gray / Orange)
        self.status_dot = QLabel()
        self.status_dot.setProperty("class", "status-dot-idle")
        header_layout.addWidget(self.status_dot)

        # Brand Title
        app_title = QLabel("AirCasta")
        app_title.setProperty("class", "brand-title")
        header_layout.addWidget(app_title)

        # Divider
        divider = QLabel("/")
        divider.setStyleSheet("color: #3f3f46; font-size: 14px;")
        header_layout.addWidget(divider)

        # Editable Device Name
        server_name = self.config.get("server_name", "AirCasta")
        self.name_edit = QLineEdit(server_name)
        self.name_edit.setPlaceholderText("Имя устройства")
        self.name_edit.setToolTip("Имя приёмника, отображаемое на iPhone (нажмите Enter для сохранения)")
        self.name_edit.setFixedWidth(190)
        self.name_edit.returnPressed.connect(self._on_name_saved)
        header_layout.addWidget(self.name_edit)

        # Subtle Network IP badge
        self.ip_label = QLabel(self.engine.lan_ip)
        self.ip_label.setProperty("class", "subtle-label")
        self.ip_label.setStyleSheet("padding: 2px 6px; background-color: #18191d; border-radius: 4px;")
        header_layout.addWidget(self.ip_label)

        # Mode Switcher (AirPlay Mirroring vs AirDrop File Transfer)
        self.mode_container = QFrame()
        self.mode_container.setStyleSheet("""
            QFrame {
                background-color: #141518;
                border: 1px solid #27272a;
                border-radius: 6px;
                padding: 1px;
            }
        """)
        mode_layout = QHBoxLayout(self.mode_container)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(2)

        self.btn_mode_airplay = QPushButton("Экран")
        self.btn_mode_airplay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_airplay.setProperty("class", "btn-tab-active")
        self.btn_mode_airplay.clicked.connect(lambda: self._switch_mode(0))
        mode_layout.addWidget(self.btn_mode_airplay)

        self.btn_mode_airdrop = QPushButton("DropCast")
        self.btn_mode_airdrop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_airdrop.setProperty("class", "btn-tab-inactive")
        self.btn_mode_airdrop.clicked.connect(lambda: self._switch_mode(1))
        mode_layout.addWidget(self.btn_mode_airdrop)

        header_layout.addWidget(self.mode_container)

        header_layout.addStretch()

        # Action Buttons
        self.diag_btn = QPushButton("Сеть")
        self.diag_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.diag_btn.clicked.connect(self._open_diagnostics)
        header_layout.addWidget(self.diag_btn)

        self.settings_btn = QPushButton("Настройки")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self._open_settings)
        header_layout.addWidget(self.settings_btn)

        # Start / Stop Toggle
        self.power_btn = QPushButton("Запустить")
        self.power_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.power_btn.setProperty("class", "btn-primary")
        self.power_btn.setMinimumWidth(94)
        self.power_btn.clicked.connect(self._toggle_power)
        header_layout.addWidget(self.power_btn)

        main_layout.addWidget(header)

        # 2. Main Center Canvas (Stacked: Screen Mirroring vs AirDrop Transfer)
        self.stack = QStackedWidget()

        # Page 0: AirPlay Video Mirroring
        self.video_widget = VideoDisplayWidget()
        self.video_widget.set_device_name(server_name)
        self._update_quality_display()
        self.stack.addWidget(self.video_widget)

        # Page 1: DropCast File Transfer
        self.airdrop_widget = DropCastWidget(self.airdrop_server)
        self.stack.addWidget(self.airdrop_widget)

        main_layout.addWidget(self.stack, 1)

        # Keyboard shortcuts
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        fs_action = QAction(self)
        fs_action.setShortcuts([QKeySequence("Alt+Return"), QKeySequence("F11")])
        fs_action.triggered.connect(self._toggle_fullscreen)
        self.addAction(fs_action)

        esc_action = QAction(self)
        esc_action.setShortcut(QKeySequence("Escape"))
        esc_action.triggered.connect(self._exit_fullscreen)
        self.addAction(esc_action)

    def _connect_signals(self):
        self.engine.state_changed.connect(self._on_engine_state_changed)
        self.engine.client_connected.connect(self._on_client_connected)
        self.engine.client_disconnected.connect(self._on_client_disconnected)
        self.engine.pin_requested.connect(self.video_widget.show_pin)
        self.engine.telemetry_updated.connect(self.video_widget.update_telemetry)
        self.video_widget.fullscreen_requested.connect(self._toggle_fullscreen)

        # AirDrop signals
        self.airdrop_server.file_received.connect(self._on_airdrop_file_received)
        self.airdrop_server.clipboard_received.connect(self._on_airdrop_clipboard_received)

    def _switch_mode(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.btn_mode_airplay.setProperty("class", "btn-tab-active")
            self.btn_mode_airdrop.setProperty("class", "btn-tab-inactive")
        else:
            self.btn_mode_airplay.setProperty("class", "btn-tab-inactive")
            self.btn_mode_airdrop.setProperty("class", "btn-tab-active")
            self.btn_mode_airdrop.setText("DropCast")

        self.btn_mode_airplay.style().unpolish(self.btn_mode_airplay)
        self.btn_mode_airplay.style().polish(self.btn_mode_airplay)
        self.btn_mode_airdrop.style().unpolish(self.btn_mode_airdrop)
        self.btn_mode_airdrop.style().polish(self.btn_mode_airdrop)

    def _on_airdrop_file_received(self, tf: TransferredFile):
        if self.stack.currentIndex() != 1:
            total = len(self.airdrop_server.received_files)
            self.btn_mode_airdrop.setText(f"DropCast ({total})")

    def _on_airdrop_clipboard_received(self, text: str):
        if text:
            QApplication.clipboard().setText(text)

    def _auto_start_engine(self):
        self.engine.start()

    def _toggle_power(self):
        if self.engine.state == EngineState.STOPPED:
            self.config.set("airplay_enabled", True)
            self.engine.start()
        else:
            self.config.set("airplay_enabled", False)
            self.engine.stop()

    def _on_name_saved(self):
        new_name = self.name_edit.text().strip()
        if new_name and new_name != self.config.get("server_name"):
            self.config.set("server_name", new_name)
            self.video_widget.set_device_name(new_name)
            if hasattr(self, "airdrop_server"):
                self.airdrop_server.set_pc_name(new_name)
            self.name_edit.clearFocus()
            if self.engine.state != EngineState.STOPPED:
                self.engine.stop()
                QTimer.singleShot(300, self.engine.start)

    def _on_engine_state_changed(self, state: EngineState):
        self.video_widget.set_stream_state(state, self.engine.client_info)
        if state in (EngineState.BROADCASTING, EngineState.STREAMING):
            self.status_dot.setProperty("class", "status-dot-active")
            self.power_btn.setText("Остановить")
            self.power_btn.setProperty("class", "")
        elif state == EngineState.CONNECTING:
            self.status_dot.setProperty("class", "status-dot-active")
            self.power_btn.setText("Остановить")
        else:
            self.status_dot.setProperty("class", "status-dot-idle")
            self.power_btn.setText("Запустить")
            self.power_btn.setProperty("class", "btn-primary")

        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)
        self.power_btn.style().unpolish(self.power_btn)
        self.power_btn.style().polish(self.power_btn)

    def _on_client_connected(self, info: ClientSessionInfo):
        if self.config.get("fullscreen_on_connect", False):
            self.showFullScreen()

    def _on_client_disconnected(self):
        self.video_widget.show_pin("")

    def _update_quality_display(self):
        res = self.config.get("video_resolution", "1920x1080")
        fps = self.config.get("max_fps", 60)
        h265 = self.config.get("h265_support", True)
        self.video_widget.set_quality_info(res, fps, h265)

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            new_name = self.config.get("server_name", "AirCasta")
            self.name_edit.setText(new_name)
            self.video_widget.set_device_name(new_name)
            if hasattr(self, "airdrop_server"):
                self.airdrop_server.set_pc_name(new_name)
                save_path = self.config.get("airdrop_save_path", str(Path.home() / "Downloads" / "AirCasta"))
                self.airdrop_server.set_save_directory(save_path)
                self.airdrop_widget.path_label.setText(save_path)
            self._update_quality_display()
            if self.engine.state != EngineState.STOPPED:
                self.engine.stop()
                QTimer.singleShot(300, self.engine.start)

    def _open_diagnostics(self):
        bin_path = str(self.engine.locate_binary() or "")
        dlg = DiagnosticsDialog(bin_path, self)
        dlg.exec()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()

    def closeEvent(self, event):
        self.engine.stop()
        if hasattr(self, "airdrop_server"):
            self.airdrop_server.stop()
        event.accept()
