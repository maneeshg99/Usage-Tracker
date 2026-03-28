"""Main floating widget that displays LLM usage data."""

from datetime import datetime, timezone

from PyQt5.QtCore import Qt, QPoint, QSize, QRect, pyqtSignal
from PyQt5.QtGui import QFont, QCursor, QPainter, QColor, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .providers.base import ProviderUsage, UsageTier
from .styles import DARK_THEME, progress_bar_color, progress_bar_glow

_RESIZE_MARGIN = 6  # px edge zone for resize handles


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
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet(DARK_THEME)
        self.setMinimumSize(280, 200)
        self.resize(340, 420)

        self._drag_pos: QPoint | None = None
        self._last_updated: datetime | None = None
        self._resizing = False
        self._resize_edge = None

        self._build_ui()

    # ── UI construction ─────────────────────────────────────────────

    def _build_ui(self):
        # Outer wrapper for the rounded-corner background
        self._bg = QFrame(self)
        self._bg.setObjectName("MainWidget")

        root = QVBoxLayout(self._bg)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(0)

        # Title bar
        title_bar = QHBoxLayout()
        title_bar.setSpacing(2)

        title = QLabel("LLM Usage Tracker")
        title.setObjectName("TitleLabel")
        title_bar.addWidget(title)
        title_bar.addStretch()

        self._settings_btn = QPushButton("\u2699")
        self._settings_btn.setObjectName("SettingsBtn")
        self._settings_btn.setToolTip("Settings")
        self._settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._settings_btn.clicked.connect(self.settings_requested.emit)
        title_bar.addWidget(self._settings_btn)

        self._refresh_btn = QPushButton("\u21bb")
        self._refresh_btn.setObjectName("RefreshBtn")
        self._refresh_btn.setToolTip("Refresh now")
        self._refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._refresh_btn.clicked.connect(self.refresh_requested.emit)
        title_bar.addWidget(self._refresh_btn)

        min_btn = QPushButton("\u2013")  # en-dash as minimize
        min_btn.setObjectName("MinBtn")
        min_btn.setToolTip("Minimize")
        min_btn.setCursor(QCursor(Qt.PointingHandCursor))
        min_btn.clicked.connect(self.showMinimized)
        title_bar.addWidget(min_btn)

        close_btn = QPushButton("\u2715")
        close_btn.setObjectName("CloseBtn")
        close_btn.setToolTip("Close")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.clicked.connect(self.close)
        title_bar.addWidget(close_btn)

        root.addLayout(title_bar)
        root.addSpacing(6)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        scroll.setWidget(self._content)
        root.addWidget(scroll, 1)

        # Status bar
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 4, 0, 0)
        self._status_label = QLabel("Waiting for data...")
        self._status_label.setObjectName("StatusLabel")
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        root.addLayout(status_row)

        # Outer layout to position _bg inside self
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)  # shadow margin
        outer.addWidget(self._bg)

        # Placeholder
        self._placeholder = QLabel(
            "No providers configured.\nClick \u2699 to add one."
        )
        self._placeholder.setObjectName("DetailLabel")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setWordWrap(True)
        self._placeholder.setStyleSheet("padding: 24px; font-size: 12px;")
        self._content_layout.addWidget(self._placeholder)
        self._content_layout.addStretch()

    # ── public API ──────────────────────────────────────────────────

    def update_usage(self, results: list[ProviderUsage]):
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
            self._add_provider_card(usage)

        self._content_layout.addStretch()
        self._status_label.setText(
            f"Updated {self._last_updated.strftime('%H:%M:%S')}"
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

    def _add_provider_card(self, usage: ProviderUsage):
        card = QFrame()
        card.setObjectName("ProviderCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        # Provider header
        provider_label = QLabel(usage.provider_name.upper())
        provider_label.setObjectName("ProviderLabel")
        card_layout.addWidget(provider_label)

        if usage.error:
            err = QLabel(usage.error)
            err.setObjectName("ErrorLabel")
            err.setWordWrap(True)
            card_layout.addWidget(err)
        else:
            for tier in usage.tiers:
                self._add_tier(card_layout, tier)

        self._content_layout.addWidget(card)

    def _add_tier(self, layout: QVBoxLayout, tier: UsageTier):
        # Tier header row: label + percentage
        header = QHBoxLayout()
        header.setContentsMargins(0, 4, 0, 0)

        label = QLabel(tier.label)
        label.setObjectName("TierLabel")
        header.addWidget(label)

        header.addStretch()

        pct = max(0.0, min(100.0, tier.used_percent))
        pct_label = QLabel(f"{pct:.0f}%")
        pct_label.setObjectName("PercentLabel")
        color = progress_bar_color(tier.used_percent)
        pct_label.setStyleSheet(f"color: {color};")
        header.addWidget(pct_label)

        layout.addLayout(header)

        # Progress bar with glow background
        bar_container = QFrame()
        bar_container.setStyleSheet(
            f"background-color: {progress_bar_glow(tier.used_percent)};"
            "border-radius: 5px; padding: 0px;"
        )
        bar_layout = QVBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)

        bar = QProgressBar()
        bar.setRange(0, 1000)  # finer granularity
        bar.setValue(max(0, min(1000, int(pct * 10))))
        bar.setTextVisible(False)
        bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 5px; }}"
        )
        bar_layout.addWidget(bar)
        layout.addWidget(bar_container)

        # Detail + reset row
        info = QHBoxLayout()
        info.setContentsMargins(0, 0, 0, 2)

        if tier.detail:
            detail = QLabel(tier.detail)
            detail.setObjectName("DetailLabel")
            info.addWidget(detail)

        info.addStretch()

        reset_text = self._format_reset(tier.reset_at)
        if reset_text:
            reset_label = QLabel(reset_text)
            reset_label.setObjectName("ResetLabel")
            info.addWidget(reset_label)

        layout.addLayout(info)

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
            return f"Resets in {days}d {hours}h"
        if hours > 0:
            return f"Resets in {hours}h {minutes}m"
        return f"Resets in {minutes}m"

    # ── painting (translucent background with rounded corners) ──────

    def paintEvent(self, event):
        # Draw nothing on the outer widget – _bg handles the background
        pass

    # ── drag support (title bar area only) ──────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge = self._edge_at(event.pos())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._resize_origin = event.globalPos()
                self._resize_geom = self.geometry()
                event.accept()
            else:
                # Only drag from top 36px (title bar)
                if event.pos().y() <= 36:
                    self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_edge:
            self._do_resize(event.globalPos())
            event.accept()
        elif self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            # Update cursor for resize zones
            edge = self._edge_at(event.pos())
            if edge in ("left", "right"):
                self.setCursor(Qt.SizeHorCursor)
            elif edge in ("top", "bottom"):
                self.setCursor(Qt.SizeVerCursor)
            elif edge in ("top-left", "bottom-right"):
                self.setCursor(Qt.SizeFDiagCursor)
            elif edge in ("top-right", "bottom-left"):
                self.setCursor(Qt.SizeBDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resizing = False
        self._resize_edge = None
        self.setCursor(Qt.ArrowCursor)

    # ── resize helpers ──────────────────────────────────────────────

    def _edge_at(self, pos: QPoint) -> str | None:
        m = _RESIZE_MARGIN
        r = self.rect()
        left = pos.x() <= m
        right = pos.x() >= r.width() - m
        top = pos.y() <= m
        bottom = pos.y() >= r.height() - m

        if top and left:
            return "top-left"
        if top and right:
            return "top-right"
        if bottom and left:
            return "bottom-left"
        if bottom and right:
            return "bottom-right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _do_resize(self, global_pos: QPoint):
        dx = global_pos.x() - self._resize_origin.x()
        dy = global_pos.y() - self._resize_origin.y()
        g = QRect(self._resize_geom)
        minw, minh = self.minimumWidth(), self.minimumHeight()
        edge = self._resize_edge

        if "right" in edge:
            g.setWidth(max(minw, g.width() + dx))
        if "bottom" in edge:
            g.setHeight(max(minh, g.height() + dy))
        if "left" in edge:
            new_w = max(minw, g.width() - dx)
            g.setLeft(g.right() - new_w)
        if "top" in edge:
            new_h = max(minh, g.height() - dy)
            g.setTop(g.bottom() - new_h)

        self.setGeometry(g)
