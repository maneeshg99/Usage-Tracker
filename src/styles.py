"""Dark theme QSS styles for the usage tracker widget."""

DARK_THEME = """
QWidget#MainWidget {
    background-color: #1a1a2e;
    border: 1px solid #16213e;
    border-radius: 12px;
}

QLabel {
    color: #e0e0e0;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}

QLabel#TitleLabel {
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
}

QLabel#ProviderLabel {
    color: #a0c4ff;
    font-size: 13px;
    font-weight: bold;
    padding-top: 8px;
}

QLabel#TierLabel {
    color: #cccccc;
    font-size: 11px;
    font-weight: 600;
}

QLabel#DetailLabel {
    color: #999999;
    font-size: 10px;
}

QLabel#ResetLabel {
    color: #888888;
    font-size: 10px;
    font-style: italic;
}

QLabel#ErrorLabel {
    color: #ff6b6b;
    font-size: 11px;
}

QLabel#StatusLabel {
    color: #777777;
    font-size: 10px;
}

QProgressBar {
    background-color: #2a2a4a;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    border-radius: 4px;
}

QPushButton#SettingsBtn, QPushButton#RefreshBtn, QPushButton#CloseBtn {
    background: transparent;
    border: none;
    color: #888888;
    font-size: 14px;
    padding: 2px 6px;
}

QPushButton#SettingsBtn:hover, QPushButton#RefreshBtn:hover {
    color: #ffffff;
}

QPushButton#CloseBtn:hover {
    color: #ff6b6b;
}

QFrame#Separator {
    background-color: #2a2a4a;
    max-height: 1px;
}
"""

SETTINGS_THEME = """
QDialog {
    background-color: #1a1a2e;
}

QLabel {
    color: #e0e0e0;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
}

QLabel#SectionLabel {
    color: #a0c4ff;
    font-size: 13px;
    font-weight: bold;
}

QLineEdit, QSpinBox {
    background-color: #2a2a4a;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    color: #e0e0e0;
    padding: 6px 10px;
    font-size: 12px;
}

QLineEdit:focus, QSpinBox:focus {
    border-color: #a0c4ff;
}

QComboBox {
    background-color: #2a2a4a;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    color: #e0e0e0;
    padding: 6px 10px;
    font-size: 12px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #2a2a4a;
    color: #e0e0e0;
    selection-background-color: #3a3a6a;
}

QPushButton {
    background-color: #3a3a6a;
    border: none;
    border-radius: 6px;
    color: #e0e0e0;
    padding: 8px 16px;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #4a4a8a;
}

QPushButton#SaveBtn {
    background-color: #2d6a4f;
}

QPushButton#SaveBtn:hover {
    background-color: #3d8a6f;
}

QPushButton#DeleteBtn {
    background-color: #6a2d2d;
}

QPushButton#DeleteBtn:hover {
    background-color: #8a3d3d;
}

QTextEdit {
    background-color: #2a2a4a;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    color: #bbbbbb;
    font-size: 10px;
    padding: 6px;
}
"""


def progress_bar_color(percent: float) -> str:
    """Return a QSS chunk color based on usage percentage."""
    if percent >= 85:
        return "#ff6b6b"  # Red
    elif percent >= 60:
        return "#ffd93d"  # Yellow
    else:
        return "#6bcb77"  # Green
