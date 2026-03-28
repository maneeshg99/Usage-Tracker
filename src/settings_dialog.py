"""Settings dialog for configuring LLM providers and credentials."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import auth, config
from .styles import SETTINGS_THEME

SESSION_TOKEN_HELP = {
    "anthropic": (
        "Manual fallback — how to get your session token:\n"
        "1. Log in to claude.ai in your browser\n"
        "2. Open DevTools (F12) -> Application tab\n"
        "3. Under Cookies -> claude.ai, find 'sessionKey'\n"
        "4. Copy the full value and paste it above"
    ),
    "openai": (
        "Manual fallback — how to get your session token:\n"
        "1. Log in to chatgpt.com in your browser\n"
        "2. Open DevTools (F12) -> Application tab\n"
        "3. Under Cookies -> chatgpt.com, find\n"
        "   '__Secure-next-auth.session-token'\n"
        "4. Copy the full value and paste it above"
    ),
}


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Usage Tracker Settings")
        self.setMinimumWidth(440)
        self.setMinimumHeight(520)
        self.setStyleSheet(SETTINGS_THEME)
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        tabs = QTabWidget()

        # Anthropic tab
        self._anthropic_tab = self._create_provider_tab("anthropic")
        tabs.addTab(self._anthropic_tab, "Anthropic (Claude)")

        # OpenAI tab
        self._openai_tab = self._create_provider_tab("openai")
        tabs.addTab(self._openai_tab, "OpenAI (ChatGPT)")

        # General tab
        general = QWidget()
        gen_layout = QFormLayout(general)
        gen_layout.setSpacing(10)

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 60)
        self._interval_spin.setSuffix(" min")
        gen_layout.addRow("Refresh interval:", self._interval_spin)

        tabs.addTab(general, "General")

        layout.addWidget(tabs)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setObjectName("SaveBtn")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

    def _create_provider_tab(self, provider_key: str) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # ── Auto-extract section (primary) ──────────────────────────
        auto_label = QLabel("Recommended: auto-extract from your browser")
        auto_label.setObjectName("SectionLabel")
        layout.addWidget(auto_label)

        auto_desc = QLabel(
            "If you're logged in to "
            + ("claude.ai" if provider_key == "anthropic" else "chatgpt.com")
            + " in Chrome, Edge, or Firefox,\nclick below to import your session automatically."
        )
        auto_desc.setWordWrap(True)
        auto_desc.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(auto_desc)

        auto_btn = QPushButton("Auto-Extract from Browser")
        auto_btn.setObjectName("SaveBtn")  # reuse green style
        auto_btn.setStyleSheet(
            "QPushButton { background-color: #2d6a4f; padding: 10px; font-size: 13px; }"
            "QPushButton:hover { background-color: #3d8a6f; }"
        )
        layout.addWidget(auto_btn)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._status_label)

        # ── Divider ─────────────────────────────────────────────────
        divider = QLabel("— or configure manually —")
        divider.setAlignment(Qt.AlignCenter)
        divider.setStyleSheet("color: #555; font-size: 10px; padding: 6px 0;")
        layout.addWidget(divider)

        # ── Auth type ───────────────────────────────────────────────
        auth_row = QHBoxLayout()
        auth_label = QLabel("Auth method:")
        auth_combo = QComboBox()
        auth_combo.addItems(["Session Token", "API Key"])
        auth_row.addWidget(auth_label)
        auth_row.addWidget(auth_combo)
        layout.addLayout(auth_row)

        # Credential input
        cred_input = QLineEdit()
        cred_input.setEchoMode(QLineEdit.Password)
        cred_input.setPlaceholderText("Paste your session token here...")
        layout.addWidget(cred_input)

        # Show/hide toggle
        show_btn = QPushButton("Show")
        show_btn.setCheckable(True)
        show_btn.toggled.connect(
            lambda checked: cred_input.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        show_btn.toggled.connect(
            lambda checked: show_btn.setText("Hide" if checked else "Show")
        )
        layout.addWidget(show_btn)

        # Help text (shown for session token mode)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(100)
        help_text.setPlainText(SESSION_TOKEN_HELP.get(provider_key, ""))
        layout.addWidget(help_text)

        def on_auth_changed(index):
            if index == 0:  # Session Token
                help_text.setVisible(True)
                cred_input.setPlaceholderText("Paste your session token here...")
            else:  # API Key
                help_text.setVisible(False)
                cred_input.setPlaceholderText("Paste your API key here...")

        auth_combo.currentIndexChanged.connect(on_auth_changed)
        help_text.setVisible(auth_combo.currentIndex() == 0)

        # Delete config button
        delete_btn = QPushButton("Remove Configuration")
        delete_btn.setObjectName("DeleteBtn")
        delete_btn.clicked.connect(lambda: self._delete_provider(provider_key, cred_input))
        layout.addWidget(delete_btn)

        layout.addStretch()

        # Wire up auto-extract button
        auto_btn.clicked.connect(lambda: self._auto_extract(provider_key, cred_input))

        # Store references
        tab.auth_combo = auth_combo
        tab.cred_input = cred_input
        tab.provider_key = provider_key

        return tab

    def _auto_extract(self, provider_key: str, cred_input: QLineEdit):
        """Attempt to auto-extract session token from browser cookies."""
        token, info = auth.extract_token(provider_key)
        if token:
            cred_input.setText(token)
            # Set auth type to Session Token
            tab = self._anthropic_tab if provider_key == "anthropic" else self._openai_tab
            tab.auth_combo.setCurrentIndex(0)  # Session Token
            QMessageBox.information(
                self,
                "Success",
                f"Session token extracted from {info}!\n\n"
                "Click Save to apply.",
            )
        else:
            QMessageBox.warning(
                self,
                "Auto-Extract Failed",
                info or "Could not find session token.",
            )

    def _load_current(self):
        """Load existing config into the dialog."""
        self._interval_spin.setValue(config.get_refresh_interval())

        for tab, key in [
            (self._anthropic_tab, "anthropic"),
            (self._openai_tab, "openai"),
        ]:
            prov = config.get_provider(key)
            if prov:
                if prov["auth_type"] == "api_key":
                    tab.auth_combo.setCurrentIndex(1)
                else:
                    tab.auth_combo.setCurrentIndex(0)
                tab.cred_input.setText(prov["credential"])

    def _save(self):
        """Save all settings."""
        config.set_refresh_interval(self._interval_spin.value())

        for tab, key in [
            (self._anthropic_tab, "anthropic"),
            (self._openai_tab, "openai"),
        ]:
            cred = tab.cred_input.text().strip()
            if cred:
                auth_type = "api_key" if tab.auth_combo.currentIndex() == 1 else "session_token"
                config.save_provider(key, auth_type, cred)

        self.accept()

    def _delete_provider(self, key: str, cred_input: QLineEdit):
        reply = QMessageBox.question(
            self,
            "Remove Provider",
            f"Remove {key} configuration?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            config.remove_provider(key)
            cred_input.clear()
