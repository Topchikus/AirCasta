"""
AirCasta - Minimalist Studio Theme
Refined, distraction-free native dark aesthetic inspired by modern pro tools.
No loud gradients, no AI slop, no emoji clutter.
"""

MINIMALIST_THEME_QSS = """
/* Base Window & Global Reset */
QMainWindow, QDialog {
    background-color: #0c0d0e;
    color: #e4e4e7;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Roboto, sans-serif;
    font-size: 13px;
}

QWidget {
    outline: none;
}

QLabel {
    background: transparent;
    color: #e4e4e7;
}

/* Header & Panels */
QFrame.header-panel {
    background-color: #121316;
    border-bottom: 1px solid #202226;
}

QFrame.bottom-panel {
    background-color: #121316;
    border-top: 1px solid #202226;
}

QFrame.canvas-frame {
    background-color: #0c0d0e;
    border: none;
}

QFrame.diag-card {
    background-color: #121316;
    border: 1px solid #202226;
    border-radius: 6px;
}

QFrame.diag-card QLabel {
    background: transparent;
    border: none;
}

/* Typography Hierarchy */
QLabel.brand-title {
    font-size: 15px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.3px;
}

QLabel.subtle-label {
    font-size: 12px;
    color: #71717a;
}

QLabel.secondary-label {
    font-size: 12px;
    color: #a1a1aa;
}

QLabel.status-dot-active {
    background-color: #10b981;
    border-radius: 4px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
}

QLabel.status-dot-idle {
    background-color: #52525b;
    border-radius: 4px;
    min-width: 8px;
    max-width: 8px;
    min-height: 8px;
    max-height: 8px;
}

/* Minimal Buttons */
QPushButton {
    background-color: #18191d;
    color: #d4d4d8;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #222328;
    color: #ffffff;
    border-color: #3f3f46;
}

QPushButton:pressed {
    background-color: #141518;
}

QPushButton.btn-primary {
    background-color: #ffffff;
    color: #0c0d0e;
    border: 1px solid #ffffff;
    font-weight: 600;
}

QPushButton.btn-primary:hover {
    background-color: #e4e4e7;
    border-color: #e4e4e7;
}

QPushButton.btn-subtle {
    background-color: transparent;
    color: #a1a1aa;
    border: none;
    padding: 5px 8px;
}

QPushButton.btn-subtle:hover {
    background-color: #1c1d22;
    color: #ffffff;
}

QPushButton.btn-tab-active {
    background-color: #27272a;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 4px;
    padding: 3px 10px;
}

QPushButton.btn-tab-inactive {
    background-color: transparent;
    color: #a1a1aa;
    font-weight: 500;
    border: none;
    border-radius: 4px;
    padding: 3px 10px;
}

QPushButton.btn-tab-inactive:hover {
    color: #ffffff;
    background-color: #1a1b1f;
}

/* Inputs */
QLineEdit {
    background-color: #141518;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 5px 10px;
    color: #f4f4f5;
    font-size: 12px;
}

QLineEdit:focus {
    border: 1px solid #52525b;
    background-color: #18191d;
}

QComboBox {
    background-color: #141518;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 5px 10px;
    color: #f4f4f5;
    font-size: 12px;
}

QComboBox:hover {
    border-color: #3f3f46;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #18191d;
    border: 1px solid #27272a;
    color: #f4f4f5;
    selection-background-color: #27272a;
    padding: 4px;
}

QSpinBox {
    background-color: #141518;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 5px 10px;
    color: #f4f4f5;
    font-size: 12px;
}

QCheckBox {
    color: #d4d4d8;
    font-size: 12px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #3f3f46;
    border-radius: 3px;
    background-color: #141518;
}

QCheckBox::indicator:checked {
    background-color: #ffffff;
    border-color: #ffffff;
}

/* Clean Slider */
QSlider::groove:horizontal {
    height: 4px;
    background: #27272a;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #71717a;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #e4e4e7;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}

QSlider::handle:horizontal:hover {
    background: #ffffff;
}

/* PIN Badge */
QLabel.pin-code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 4px;
    color: #ffffff;
    background-color: #18191d;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 6px 16px;
}

/* Dialogs & Tabs */
QGroupBox {
    border: 1px solid #222328;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 14px;
    font-weight: 600;
    color: #d4d4d8;
    font-size: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    background-color: #0c0d0e;
}

QScrollArea {
    border: 1px solid #202226;
    border-radius: 6px;
    background-color: #0e0f12;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
}

QScrollBar::handle:vertical {
    background: #27272a;
    border-radius: 3px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #3f3f46;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

# Alias for backward compatibility
DARK_THEME_QSS = MINIMALIST_THEME_QSS
