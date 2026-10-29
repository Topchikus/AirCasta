"""
AirCasta - Minimalist DropCast UI View
Provides QR code scanning for iPhone, Drag & Drop file sharing (PC -> iPhone),
and real-time reception of photos, videos, and documents (iPhone -> PC).
"""

import os
import platform
import subprocess
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import qrcode
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QDragEnterEvent, QDropEvent, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
)

from airdrop_backend.server import DropCastServer, TransferredFile


def format_bytes(bytes_count: int) -> str:
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


def get_file_type_symbol(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in (".jpg", ".jpeg", ".png", ".heic", ".gif", ".webp", ".raw", ".dng"):
        return "🖼"
    elif ext in (".mp4", ".mov", ".mkv", ".avi", ".webm"):
        return "🎬"
    elif ext in (".mp3", ".m4a", ".wav", ".aac", ".flac"):
        return "🎵"
    elif ext in (".zip", ".rar", ".7z", ".tar", ".gz"):
        return "📦"
    elif ext in (".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx"):
        return "📄"
    return "📁"


class DropTargetFrame(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setProperty("class", "drop-zone")
        self.setStyleSheet("""
            QFrame.drop-zone {
                background-color: #121316;
                border: 1px dashed #3f3f46;
                border-radius: 8px;
                padding: 16px;
            }
            QFrame.drop-zone:hover {
                border-color: #71717a;
                background-color: #16171b;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame.drop-zone {
                    background-color: #18191e;
                    border: 1px dashed #38bdf8;
                    border-radius: 8px;
                    padding: 16px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame.drop-zone {
                background-color: #121316;
                border: 1px dashed #3f3f46;
                border-radius: 8px;
                padding: 16px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        self.dragLeaveEvent(None)
        if file_paths:
            self.files_dropped.emit(file_paths)


class DropCastWidget(QWidget):
    def __init__(self, server: DropCastServer, parent=None):
        super().__init__(parent)
        self.server = server
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(20)

        # ==========================================
        # LEFT COLUMN: QR Code, URL & Folder Config
        # ==========================================
        left_card = QFrame()
        left_card.setProperty("class", "diag-card")
        left_card.setFixedWidth(290)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(12)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title = QLabel("DropCast")
        title.setProperty("class", "brand-title")
        subtitle = QLabel("Беспроводная передача с iPhone")
        subtitle.setProperty("class", "subtle-label")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        left_layout.addLayout(title_box)

        # QR Code Container
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setFixedSize(200, 200)
        self.qr_label.setStyleSheet("background-color: #18191d; border-radius: 8px; border: 1px solid #27272a;")
        
        qr_wrap = QHBoxLayout()
        qr_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_wrap.addWidget(self.qr_label)
        left_layout.addLayout(qr_wrap)

        # Hint under QR
        hint = QLabel("Наведите камеру iPhone на QR-код для открытия в Safari")
        hint.setProperty("class", "subtle-label")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(hint)

        # Link Pill + Copy Button
        link_row = QHBoxLayout()
        link_row.setSpacing(6)
        self.url_label = QLabel(self.server.url)
        self.url_label.setStyleSheet("font-family: monospace; font-size: 11px; color: #a1a1aa; padding: 4px 8px; background: #141518; border-radius: 4px;")
        self.url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        link_row.addWidget(self.url_label, 1)

        self.copy_url_btn = QPushButton("Копия")
        self.copy_url_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_url_btn.clicked.connect(self._copy_url)
        link_row.addWidget(self.copy_url_btn)
        left_layout.addLayout(link_row)

        # Firewall helper button if iPhone can't open
        fw_box = QVBoxLayout()
        fw_box.setSpacing(4)
        fw_hint = QLabel("Не открывается страница на iPhone?")
        fw_hint.setStyleSheet("font-size: 11px; color: #71717a;")
        fw_box.addWidget(fw_hint)

        self.fix_fw_btn = QPushButton("Разрешить в Брандмауэре")
        self.fix_fw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fix_fw_btn.setToolTip("Разрешает порт 7080 и Python в домашней сети Windows")
        self.fix_fw_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(56, 189, 248, 0.1);
                border: 1px solid rgba(56, 189, 248, 0.3);
                color: #38bdf8;
                font-size: 11px;
                padding: 6px 10px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(56, 189, 248, 0.2);
                border-color: #38bdf8;
            }
        """)
        self.fix_fw_btn.clicked.connect(self._fix_firewall)
        fw_box.addWidget(self.fix_fw_btn)
        left_layout.addLayout(fw_box)

        # Save Directory Card
        folder_box = QVBoxLayout()
        folder_box.setSpacing(6)
        folder_title = QLabel("Папка сохранения DropCast")
        folder_title.setProperty("class", "subtle-label")
        folder_box.addWidget(folder_title)

        self.path_label = QLabel(str(self.server.save_directory))
        self.path_label.setStyleSheet("font-size: 11px; color: #d4d4d8; font-weight: 500;")
        self.path_label.setWordWrap(True)
        folder_box.addWidget(self.path_label)

        f_btn_row = QHBoxLayout()
        f_btn_row.setSpacing(6)
        open_folder_btn = QPushButton("Открыть")
        open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_folder_btn.clicked.connect(self._open_save_folder)
        f_btn_row.addWidget(open_folder_btn)

        change_folder_btn = QPushButton("Изменить")
        change_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_folder_btn.clicked.connect(self._change_save_folder)
        f_btn_row.addWidget(change_folder_btn)

        folder_box.addLayout(f_btn_row)
        left_layout.addLayout(folder_box)

        main_layout.addWidget(left_card)

        # ==========================================
        # RIGHT COLUMN: Send to iPhone & History
        # ==========================================
        right_container = QVBoxLayout()
        right_container.setSpacing(14)

        # 1. Send to iPhone Drop Zone
        self.drop_target = DropTargetFrame()
        drop_layout = QVBoxLayout(self.drop_target)
        drop_layout.setContentsMargins(16, 14, 16, 14)
        drop_layout.setSpacing(10)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        drop_title = QLabel("Передать на iPhone (ПК → iPhone)")
        drop_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #f4f4f5;")
        drop_layout.addWidget(drop_title)

        drop_hint = QLabel("Перетащите файлы сюда или нажмите кнопку")
        drop_hint.setProperty("class", "subtle-label")
        drop_layout.addWidget(drop_hint)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        choose_files_btn = QPushButton("Выбрать файлы...")
        choose_files_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        choose_files_btn.setProperty("class", "btn-primary")
        choose_files_btn.clicked.connect(self._choose_files_to_send)
        btn_row.addWidget(choose_files_btn)

        self.clear_shared_btn = QPushButton("Очистить")
        self.clear_shared_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_shared_btn.clicked.connect(self._clear_shared_files)
        self.clear_shared_btn.setVisible(False)
        btn_row.addWidget(self.clear_shared_btn)
        drop_layout.addLayout(btn_row)

        self.shared_count_label = QLabel("")
        self.shared_count_label.setProperty("class", "subtle-label")
        drop_layout.addWidget(self.shared_count_label)

        self.drop_target.files_dropped.connect(self._add_files_to_share)
        right_container.addWidget(self.drop_target)

        # 2. Received Files Header
        rec_header = QHBoxLayout()
        rec_title = QLabel("Полученные файлы с iPhone")
        rec_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #f4f4f5;")
        rec_header.addWidget(rec_title)

        rec_header.addStretch()

        self.rec_count_label = QLabel("0 файлов")
        self.rec_count_label.setProperty("class", "subtle-label")
        rec_header.addWidget(self.rec_count_label)
        right_container.addLayout(rec_header)

        # 3. Received Files Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 8, 0)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.empty_label = QLabel("Пока нет полученных файлов. Отправьте фото или файлы с iPhone.")
        self.empty_label.setProperty("class", "subtle-label")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("padding: 30px 0;")
        self.scroll_layout.addWidget(self.empty_label)

        scroll.setWidget(self.scroll_content)
        right_container.addWidget(scroll, 1)

        main_layout.addLayout(right_container, 1)

        # Generate QR
        self.update_qr(self.server.url)

    def _connect_signals(self):
        self.server.file_received.connect(self._on_file_received)
        self.server.status_changed.connect(self._on_server_status_changed)

    def update_qr(self, url: str):
        try:
            qr = qrcode.QRCode(box_size=5, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="white", back_color="#18191d")
            buf = BytesIO()
            img.save(buf, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            self.qr_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.url_label.setText(url)
        except Exception as e:
            print(f"[AirDrop UI] QR generation error: {e}")

    def _on_server_status_changed(self, is_running: bool, url: str):
        if is_running and url:
            self.update_qr(url)

    def _copy_url(self):
        QApplication.clipboard().setText(self.server.url)
        self.copy_url_btn.setText("Скопировано")
        self.copy_url_btn.setStyleSheet("color: #10b981;")

    def _open_save_folder(self):
        folder = str(self.server.save_directory)
        if platform.system() == "Windows":
            os.startfile(folder)
        else:
            subprocess.run(["open", folder])

    def _change_save_folder(self):
        selected = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения файлов AirDrop", str(self.server.save_directory))
        if selected:
            self.server.set_save_directory(selected)
            self.path_label.setText(selected)

    def _choose_files_to_send(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите файлы для отправки на iPhone")
        if files:
            self._add_files_to_share(files)

    def _add_files_to_share(self, file_paths: List[str]):
        count = 0
        for p in file_paths:
            tf = self.server.add_shared_file(p)
            if tf:
                count += 1

        total = len(self.server.shared_files)
        if total > 0:
            self.shared_count_label.setText(f"Готово к скачиванию на iPhone: {total} файлов")
            self.clear_shared_btn.setVisible(True)

    def _clear_shared_files(self):
        self.server.clear_shared_files()
        self.shared_count_label.setText("")
        self.clear_shared_btn.setVisible(False)

    def _on_file_received(self, tf: TransferredFile):
        if self.empty_label.isVisible():
            self.empty_label.setVisible(False)

        card = QFrame()
        card.setProperty("class", "diag-card")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(10)

        # Icon
        symbol = get_file_type_symbol(tf.name)
        icon_label = QLabel(symbol)
        icon_label.setStyleSheet("font-size: 20px;")
        card_layout.addWidget(icon_label)

        # Name and size
        detail_layout = QVBoxLayout()
        detail_layout.setSpacing(2)
        name_label = QLabel(tf.name)
        name_label.setStyleSheet("font-weight: 600; color: #f4f4f5; font-size: 13px;")
        detail_layout.addWidget(name_label)

        size_text = format_bytes(tf.size)
        if tf.speed_mbps > 0:
            size_text += f"  ·  {tf.speed_mbps:.1f} MB/s"
        meta_label = QLabel(size_text)
        meta_label.setProperty("class", "subtle-label")
        detail_layout.addWidget(meta_label)
        card_layout.addLayout(detail_layout, 1)

        # Action buttons
        open_btn = QPushButton("Открыть")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(lambda _, p=tf.path: self._open_file(p))
        card_layout.addWidget(open_btn)

        reveal_btn = QPushButton("В папке")
        reveal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reveal_btn.clicked.connect(lambda _, p=tf.path: self._reveal_file_in_explorer(p))
        card_layout.addWidget(reveal_btn)

        self.scroll_layout.insertWidget(0, card)

        total_received = len(self.server.received_files)
        self.rec_count_label.setText(f"{total_received} " + ("файл" if total_received == 1 else "файлов"))

    def _fix_firewall(self):
        import sys
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent
        else:
            base_dir = Path(__file__).resolve().parent.parent
        ps_path = base_dir / "allow_firewall.ps1"
        try:
            if ps_path.exists() and platform.system() == "Windows":
                cmd = f'Start-Process powershell -Verb RunAs -ArgumentList \'-NoProfile -ExecutionPolicy Bypass -File "{ps_path}"\''
                subprocess.Popen(["powershell", "-NoProfile", "-Command", cmd], shell=True)
            self.fix_fw_btn.setText("Запрос UAC запущен ✓")
            self.fix_fw_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(16, 185, 129, 0.15);
                    border: 1px solid #10b981;
                    color: #10b981;
                    font-size: 11px;
                    padding: 6px 10px;
                    border-radius: 6px;
                }
            """)
        except Exception as e:
            print(f"[DropCast] Firewall trigger error: {e}")

    def _open_file(self, file_path: str):
        if os.path.exists(file_path):
            if platform.system() == "Windows":
                os.startfile(file_path)
            else:
                subprocess.run(["open", file_path])

    def _reveal_file_in_explorer(self, file_path: str):
        if os.path.exists(file_path) and platform.system() == "Windows":
            subprocess.run(["explorer.exe", f"/select,{os.path.normpath(file_path)}"])


# Alias for backward compatibility
AirDropWidget = DropCastWidget
