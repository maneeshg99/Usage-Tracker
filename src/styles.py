"""Dark theme QSS styles for the usage tracker widget."""

DARK_THEME = """
QWidget#MainWidget {
    background-color: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e1e2e, stop:1 #181825
    );
    border: 1px solid rgba(69, 71, 90, 0.6);
    border-radius: 16px;
}

QLabel {
    color: #cdd6f4;
    font-family: "Segoe UI", "Helvetica Neue", "SF Pro Display", Arial, sans-serif;
}

QLabel#TitleLabel {
    color: #cdd6f4;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 0.5px;
}

QLabel#ProviderLabel {
    color: #89b4fa;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 0px;
}

QLabel#TierLabel {
    color: #bac2de;
    font-size: 11px;
    font-weight: 600;
    padding: 0px;
}

QLabel#DetailLabel {
    color: #6c7086;
    font-size: 10px;
}

QLabel#PercentLabel {
    font-size: 11px;
    font-weight: bold;
}

QLabel#ResetLabel {
    color: #6c7086;
    font-size: 10px;
}

QLabel#ErrorLabel {
    color: #f38ba8;
    font-size: 11px;
    padding: 4px 8px;
    background-color: rgba(243, 139, 168, 0.08);
    border-radius: 6px;
}

QLabel#StatusLabel {
    color: #585b70;
    font-size: 10px;
    padding-top: 4px;
}

QProgressBar {
    background-color: rgba(49, 50, 68, 0.8);
    border: none;
    border-radius: 5px;
    min-height: 10px;
    max-height: 10px;
}

QProgressBar::chunk {
    border-radius: 5px;
}

QPushButton#SettingsBtn, QPushButton#RefreshBtn, QPushButton#CloseBtn, QPushButton#MinBtn {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #6c7086;
    font-size: 14px;
    padding: 4px 7px;
    min-width: 24px;
    min-height: 24px;
}

QPushButton#SettingsBtn:hover, QPushButton#RefreshBtn:hover, QPushButton#MinBtn:hover {
    color: #cdd6f4;
    background-color: rgba(108, 112, 134, 0.15);
}

QPushButton#CloseBtn:hover {
    color: #f38ba8;
    background-color: rgba(243, 139, 168, 0.12);
}

QFrame#Separator {
    background-color: rgba(69, 71, 90, 0.4);
    max-height: 1px;
    margin-top: 4px;
    margin-bottom: 4px;
}

/* Provider card container */
QFrame#ProviderCard {
    background-color: rgba(30, 30, 46, 0.5);
    border: 1px solid rgba(69, 71, 90, 0.3);
    border-radius: 10px;
    padding: 0px;
}

QFrame#ProviderCard:hover {
    border: 1px solid rgba(137, 180, 250, 0.25);
}

/* Resize grip */
QSizeGrip {
    width: 12px;
    height: 12px;
    background: transparent;
}

/* Scrollbar */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: rgba(108, 112, 134, 0.3);
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(108, 112, 134, 0.5);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
"""

SETTINGS_THEME = """
QDialog {
    background-color: #1e1e2e;
}

QLabel {
    color: #cdd6f4;
    font-family: "Segoe UI", "Helvetica Neue", "SF Pro Display", Arial, sans-serif;
}

QLabel#SectionLabel {
    color: #89b4fa;
    font-size: 13px;
    font-weight: bold;
}

QLineEdit, QSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    color: #cdd6f4;
    padding: 8px 12px;
    font-size: 12px;
    selection-background-color: #45475a;
}

QLineEdit:focus, QSpinBox:focus {
    border-color: #89b4fa;
}

QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    color: #cdd6f4;
    padding: 8px 12px;
    font-size: 12px;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #45475a;
    border-radius: 8px;
}

QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    color: #cdd6f4;
    padding: 8px 16px;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #45475a;
    border-color: #585b70;
}

QPushButton#SaveBtn {
    background-color: #a6e3a1;
    color: #1e1e2e;
    border: none;
    font-weight: bold;
}

QPushButton#SaveBtn:hover {
    background-color: #94e2d5;
}

QPushButton#DeleteBtn {
    background-color: rgba(243, 139, 168, 0.15);
    color: #f38ba8;
    border: 1px solid rgba(243, 139, 168, 0.3);
}

QPushButton#DeleteBtn:hover {
    background-color: rgba(243, 139, 168, 0.25);
}

QTextEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    color: #a6adc8;
    font-size: 10px;
    padding: 8px;
}

QTabWidget::pane {
    border: 1px solid #45475a;
    border-radius: 8px;
    background-color: #1e1e2e;
}

QTabBar::tab {
    background: #313244;
    color: #a6adc8;
    padding: 8px 16px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: #45475a;
    color: #cdd6f4;
}

QTabBar::tab:hover:!selected {
    background: #3b3b52;
}
"""


def progress_bar_color(percent: float) -> str:
    """Return a QSS chunk color based on usage percentage (Catppuccin palette)."""
    if percent >= 85:
        return "#f38ba8"  # Red (Catppuccin Maroon)
    elif percent >= 60:
        return "#f9e2af"  # Yellow (Catppuccin Yellow)
    else:
        return "#a6e3a1"  # Green (Catppuccin Green)


def progress_bar_glow(percent: float) -> str:
    """Return a subtle glow color matching the bar."""
    if percent >= 85:
        return "rgba(243, 139, 168, 0.15)"
    elif percent >= 60:
        return "rgba(249, 226, 175, 0.10)"
    else:
        return "rgba(166, 227, 161, 0.08)"
