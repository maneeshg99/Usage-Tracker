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

from . import config
from .styles import SETTINGS_THEME

SESSION_TOKEN_HELP = {
    "anthropic": (
        "How to get your Anthropic session token:\n"
        "1. Log in to claude.ai in your browser\n"
        "2. Open DevTools (F12) → Application tab\n"
        "3. Under Cookies → claude.ai, find 'sessionKey'\n"
        "4. Copy the full value and paste it here"
    ),
    "openai": (
        "How to get your OpenAI session token:\n"
        "1. Log in to chatgpt.com in your browser\n"
        "2. Open DevTools (F12) → Application tab\n"
        "3. Under Cookies → chatgpt.com, find\n"
        "   '__Secure-next-auth.session-token'\n"
        "4. Copy the full value and paste it here"
    ),
}


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Usage Tracker Settings")
        self.setMinimumWidth(420)
        self.setMinimumHeight(480)
        self.setStyleSheet(SETTINGS_THEME)
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3a3a5a; border-radius: 6px; }
            QTabBar::tab {
                background: #2a2a4a; color: #ccc; padding: 8px 16px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background: #3a3a6a; color: #fff; }
        """)

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

        # Auth type
        auth_row = QHBoxLayout()
        auth_label = QLabel("Auth method:")
        auth_combo = QComboBox()
        auth_combo.addItems(["API Key", "Session Token"])
        auth_row.addWidget(auth_label)
        auth_row.addWidget(auth_combo)
        layout.addLayout(auth_row)

        # Credential input
        cred_label = QLabel("Credential:")
        cred_input = QLineEdit()
        cred_input.setEchoMode(QLineEdit.Password)
        cred_input.setPlaceholderText("Paste your API key or session token here...")
        layout.addWidget(cred_label)
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

        # Help text
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(120)
        help_text.setPlainText(SESSION_TOKEN_HELP.get(provider_key, ""))
        layout.addWidget(help_text)

        # Update help text when auth type changes
        def on_auth_changed(index):
            if index == 1:  # Session Token
                help_text.setVisible(True)
                cred_input.setPlaceholderText("Paste your session token here...")
            else:
                help_text.setVisible(False)
                cred_input.setPlaceholderText("Paste your API key here...")

        auth_combo.currentIndexChanged.connect(on_auth_changed)
        help_text.setVisible(auth_combo.currentIndex() == 1)

        # Delete config button
        delete_btn = QPushButton("Remove Configuration")
        delete_btn.setObjectName("DeleteBtn")
        delete_btn.clicked.connect(lambda: self._delete_provider(provider_key, cred_input))
        layout.addWidget(delete_btn)

        layout.addStretch()

        # Store references
        tab.auth_combo = auth_combo
        tab.cred_input = cred_input
        tab.provider_key = provider_key

        return tab

    def _load_current(self):
        """Load existing config into the dialog."""
        self._interval_spin.setValue(config.get_refresh_interval())

        for tab, key in [
            (self._anthropic_tab, "anthropic"),
            (self._openai_tab, "openai"),
        ]:
            prov = config.get_provider(key)
            if prov:
                idx = 1 if prov["auth_type"] == "session_token" else 0
                tab.auth_combo.setCurrentIndex(idx)
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
                auth_type = "session_token" if tab.auth_combo.currentIndex() == 1 else "api_key"
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
