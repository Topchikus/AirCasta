"""
AirCasta - Native AirPlay Mirroring Receiver for Windows and macOS
Entry point for launching the desktop application.
"""

import sys
import os
from pathlib import Path

# Ensure project root is in python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from airplay_backend.config import ConfigManager
from airplay_backend.engine import AirPlayEngine
from ui.main_window import MainWindow
from ui.styles import MINIMALIST_THEME_QSS


def main():
    # Enable High DPI scaling
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("AirCasta")
    app.setOrganizationName("AirCasta")

    # Apply modern minimalist dark stylesheet
    app.setStyleSheet(MINIMALIST_THEME_QSS)

    # Load configuration
    config = ConfigManager()

    # Initialize AirPlay backend engine
    engine = AirPlayEngine(config)

    # Create and display Main Window
    window = MainWindow(config, engine)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
