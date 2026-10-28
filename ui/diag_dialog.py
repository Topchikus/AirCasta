"""
AirCasta - Minimalist Network Diagnostics Dialog
Checks network adapters, port availability, firewall profiles, and router AP isolation.
Distraction-free, professional layout.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QVBoxLayout, QWidget
)

from airplay_backend.diagnostics import DiagnosticReport, NetworkDiagnostics


class DiagnosticsDialog(QDialog):
    def __init__(self, binary_path: str = "", parent=None):
        super().__init__(parent)
        self.binary_path = binary_path
        self.setWindowTitle("Сетевая диагностика")
        self.resize(620, 540)
        self.setModal(True)

        self._init_ui()
        self.run_checks()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. Header row
        top_row = QHBoxLayout()
        header = QLabel("Диагностика сети")
        header.setStyleSheet("font-size: 15px; font-weight: 600; color: #ffffff;")
        top_row.addWidget(header)

        top_row.addStretch()

        refresh_btn = QPushButton("Обновить")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.run_checks)
        top_row.addWidget(refresh_btn)

        main_layout.addLayout(top_row)

        desc = QLabel("Проверка сетевых интерфейсов, портов RTSP/mDNS и правил брандмауэра.")
        desc.setStyleSheet("color: #71717a; font-size: 12px;")
        main_layout.addWidget(desc)

        # 2. Scroll area for checks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 8, 12)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, 1)

        # 3. Firewall rule quick copy box (hidden if not needed)
        self.fix_box = QFrame()
        self.fix_box.setStyleSheet("""
            QFrame {
                background-color: #121316;
                border: 1px solid #27272a;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        fix_layout = QVBoxLayout(self.fix_box)
        fix_layout.setSpacing(6)

        fix_title = QLabel("Правило брандмауэра Windows (PowerShell)")
        fix_title.setStyleSheet("font-weight: 600; color: #e4e4e7; font-size: 12px;")
        fix_layout.addWidget(fix_title)

        cmd_row = QHBoxLayout()
        cmd_row.setSpacing(8)

        self.cmd_label = QLabel("")
        self.cmd_label.setStyleSheet("""
            background-color: #0c0d0e;
            color: #a1a1aa;
            border: 1px solid #202226;
            border-radius: 4px;
            padding: 6px 10px;
            font-family: ui-monospace, Consolas, monospace;
            font-size: 11px;
        """)
        self.cmd_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        cmd_row.addWidget(self.cmd_label, 1)

        self.copy_btn = QPushButton("Копировать")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_cmd)
        cmd_row.addWidget(self.copy_btn)

        fix_layout.addLayout(cmd_row)
        main_layout.addWidget(self.fix_box)

        # 4. Bottom footer
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        main_layout.addLayout(btn_layout)

    def run_checks(self):
        # Clear previous items
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        report: DiagnosticReport = NetworkDiagnostics.run_full_diagnostics(self.binary_path)

        for diag_item in report.items:
            card = QFrame()
            card.setProperty("class", "diag-card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            card_layout.setSpacing(4)

            top = QHBoxLayout()
            top.setSpacing(8)

            title = QLabel(diag_item.name)
            title.setStyleSheet("font-weight: 600; color: #f4f4f5; font-size: 12px;")
            top.addWidget(title)

            top.addStretch()

            # Status pill
            badge = QLabel(diag_item.status)
            if diag_item.status == "OK":
                badge.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 600; background: #064e3b; padding: 2px 6px; border-radius: 4px;")
            elif diag_item.status == "WARNING":
                badge.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: 600; background: #451a03; padding: 2px 6px; border-radius: 4px;")
            elif diag_item.status == "ERROR":
                badge.setStyleSheet("color: #ef4444; font-size: 11px; font-weight: 600; background: #450a0a; padding: 2px 6px; border-radius: 4px;")
            else:
                badge.setStyleSheet("color: #71717a; font-size: 11px; font-weight: 500; background: #18191d; padding: 2px 6px; border-radius: 4px;")

            top.addWidget(badge)
            card_layout.addLayout(top)

            detail = QLabel(diag_item.detail)
            detail.setStyleSheet("color: #71717a; font-size: 12px;")
            detail.setWordWrap(True)
            card_layout.addWidget(detail)

            if diag_item.recommendation:
                rec = QLabel(f"Рекомендация: {diag_item.recommendation}")
                rec.setStyleSheet("color: #a1a1aa; font-size: 11px; margin-top: 2px;")
                rec.setWordWrap(True)
                card_layout.addWidget(rec)

            self.scroll_layout.addWidget(card)

        if report.firewall_command_fix:
            self.cmd_label.setText(report.firewall_command_fix)
            self.fix_box.setVisible(True)
        else:
            self.fix_box.setVisible(False)

    def _copy_cmd(self):
        text = self.cmd_label.text()
        if text:
            QApplication.clipboard().setText(text)
            self.copy_btn.setText("Скопировано")
            self.copy_btn.setStyleSheet("color: #10b981;")
