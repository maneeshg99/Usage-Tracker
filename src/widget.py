"""Main floating widget that displays LLM usage data."""

from datetime import datetime, timezone

from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .providers.base import ProviderUsage, UsageTier
from .styles import DARK_THEME, progress_bar_color


class UsageWidget(QWidget):
    """Always-on-top floating widget showing LLM usage."""

    settings_requested = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("MainWidget")
        self.setWindowTitle("LLM Usage Tracker")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setStyleSheet(DARK_THEME)
        self.setMinimumWidth(300)
        self.setMaximumWidth(360)

        self._drag_pos: QPoint | None = None
        self._last_updated: datetime | None = None

        self._build_ui()

    # ── UI construction ─────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 10)
        root.setSpacing(0)

        # Title bar
        title_bar = QHBoxLayout()
        title_bar.setSpacing(4)
        title = QLabel("LLM Usage Tracker")
        title.setObjectName("TitleLabel")
        title_bar.addWidget(title)
        title_bar.addStretch()

        self._settings_btn = QPushButton("\u2699")  # gear
        self._settings_btn.setObjectName("SettingsBtn")
        self._settings_btn.setToolTip("Settings")
        self._settings_btn.clicked.connect(self.settings_requested.emit)
        title_bar.addWidget(self._settings_btn)

        self._refresh_btn = QPushButton("\u21bb")  # refresh
        self._refresh_btn.setObjectName("RefreshBtn")
        self._refresh_btn.setToolTip("Refresh now")
        self._refresh_btn.clicked.connect(self.refresh_requested.emit)
        title_bar.addWidget(self._refresh_btn)

        close_btn = QPushButton("\u2715")  # ×
        close_btn.setObjectName("CloseBtn")
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.close)
        title_bar.addWidget(close_btn)

        root.addLayout(title_bar)

        # Scrollable content area for provider sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 4, 0, 0)
        self._content_layout.setSpacing(2)
        scroll.setWidget(self._content)
        root.addWidget(scroll)

        # Status bar
        self._status_label = QLabel("Waiting for data...")
        self._status_label.setObjectName("StatusLabel")
        root.addWidget(self._status_label)

        # Placeholder for no-providers state
        self._placeholder = QLabel(
            "No providers configured.\nClick \u2699 to add one."
        )
        self._placeholder.setObjectName("DetailLabel")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setWordWrap(True)
        self._content_layout.addWidget(self._placeholder)
        self._content_layout.addStretch()

    # ── public API ──────────────────────────────────────────────────

    def update_usage(self, results: list[ProviderUsage]):
        """Replace displayed data with fresh results."""
        self._clear_content()
        self._last_updated = datetime.now(timezone.utc)

        if not results:
            self._placeholder.setVisible(True)
            self._content_layout.addWidget(self._placeholder)
            self._content_layout.addStretch()
            self._status_label.setText("No providers configured")
            return

        self._placeholder.setVisible(False)

        for i, usage in enumerate(results):
            if i > 0:
                sep = QFrame()
                sep.setObjectName("Separator")
                sep.setFrameShape(QFrame.HLine)
                self._content_layout.addWidget(sep)

            self._add_provider_section(usage)

        self._content_layout.addStretch()
        self._status_label.setText(
            f"Last updated: {self._last_updated.strftime('%H:%M:%S')}"
        )

    def set_loading(self):
        self._status_label.setText("Refreshing...")

    # ── internal ────────────────────────────────────────────────────

    def _clear_content(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w and w is not self._placeholder:
                w.deleteLater()

    def _add_provider_section(self, usage: ProviderUsage):
        provider_label = QLabel(usage.provider_name.upper())
        provider_label.setObjectName("ProviderLabel")
        self._content_layout.addWidget(provider_label)

        if usage.error:
            err = QLabel(usage.error)
            err.setObjectName("ErrorLabel")
            err.setWordWrap(True)
            self._content_layout.addWidget(err)
            return

        for tier in usage.tiers:
            self._add_tier(tier)

    def _add_tier(self, tier: UsageTier):
        label = QLabel(tier.label)
        label.setObjectName("TierLabel")
        self._content_layout.addWidget(label)

        # Progress bar
        bar = QProgressBar()
        bar.setRange(0, 100)
        pct = max(0, min(100, int(tier.used_percent)))
        bar.setValue(pct)
        bar.setTextVisible(False)
        color = progress_bar_color(tier.used_percent)
        bar.setStyleSheet(
            bar.styleSheet()
            + f"\nQProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}"
        )
        self._content_layout.addWidget(bar)

        # Detail + reset info row
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 4)

        if tier.detail:
            detail = QLabel(tier.detail)
            detail.setObjectName("DetailLabel")
            info_layout.addWidget(detail)

        info_layout.addStretch()

        reset_text = self._format_reset(tier.reset_at)
        if reset_text:
            reset_label = QLabel(reset_text)
            reset_label.setObjectName("ResetLabel")
            info_layout.addWidget(reset_label)

        self._content_layout.addLayout(info_layout)

    @staticmethod
    def _format_reset(reset_at: datetime | None) -> str:
        if reset_at is None:
            return ""
        now = datetime.now(timezone.utc)
        delta = reset_at - now
        if delta.total_seconds() <= 0:
            return "Resetting..."

        total_secs = int(delta.total_seconds())
        days = total_secs // 86400
        hours = (total_secs % 86400) // 3600
        minutes = (total_secs % 3600) // 60

        if days > 0:
            return f"Resets in: {days}d {hours}h"
        if hours > 0:
            return f"Resets in: {hours}h {minutes}m"
        return f"Resets in: {minutes}m"

    # ── drag support ────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
