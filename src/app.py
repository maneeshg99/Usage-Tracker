"""Application entry point – wires together the widget, providers, and config."""

import os
import sys
import threading
from typing import Optional

from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from . import config
from .providers.anthropic import AnthropicProvider
from .providers.openai_provider import OpenAIProvider
from .providers.base import ProviderUsage
from .settings_dialog import SettingsDialog
from .widget import UsageWidget, _icon_path


PROVIDERS = {
    "anthropic": AnthropicProvider(),
    "openai": OpenAIProvider(),
}


class UsageFetcher(QObject):
    """Runs provider fetches in a background thread and emits results."""

    results_ready = pyqtSignal(list)

    def fetch(self):
        thread = threading.Thread(target=self._do_fetch, daemon=True)
        thread.start()

    def _do_fetch(self):
        results: list[ProviderUsage] = []
        for key, provider in PROVIDERS.items():
            prov_cfg = config.get_provider(key)
            if prov_cfg is None or not prov_cfg.get("enabled", True):
                continue
            usage = provider.fetch_usage(prov_cfg["auth_type"], prov_cfg["credential"])
            results.append(usage)
        self.results_ready.emit(results)


class App:
    def __init__(self):
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("LLM Usage Tracker")

        # Set app-wide icon (taskbar, alt-tab, window switcher)
        icon_file = _icon_path()
        if os.path.exists(icon_file):
            self._app.setWindowIcon(QIcon(icon_file))

        self._widget = UsageWidget()
        self._fetcher = UsageFetcher()

        # Auto-refresh timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh)
        self._update_timer_interval()

        # Connections
        self._widget.settings_requested.connect(self._open_settings)
        self._widget.refresh_requested.connect(self._refresh)
        self._fetcher.results_ready.connect(self._on_results)

    def run(self) -> int:
        self._widget.show()
        self._refresh()  # Initial fetch
        self._timer.start()
        return self._app.exec_()

    def _refresh(self):
        self._widget.set_loading()
        self._fetcher.fetch()

    def _on_results(self, results: list[ProviderUsage]):
        self._widget.update_usage(results)

    def _open_settings(self):
        dlg = SettingsDialog(self._widget)
        if dlg.exec_():
            # Settings changed – refresh immediately
            self._update_timer_interval()
            self._refresh()

    def _update_timer_interval(self):
        minutes = config.get_refresh_interval()
        self._timer.setInterval(minutes * 60 * 1000)


def main():
    app = App()
    sys.exit(app.run())
