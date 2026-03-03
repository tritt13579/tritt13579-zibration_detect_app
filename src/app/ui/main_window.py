from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout

from app.config.settings import AppSettings
from app.ui.widgets.model_panel import ModelPanel
from app.ui.widgets.excel_panel import ExcelPanel
from app.ui.widgets.action_panel import ActionPanel
from app.ui.widgets.result_table import ResultTable


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.setWindowTitle(settings.app_name)
        self.resize(settings.window_width, settings.window_height)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.model_panel = ModelPanel()
        self.excel_panel = ExcelPanel()
        self.action_panel = ActionPanel()
        self.result_table = ResultTable()
        self._busy_count = 0

        layout.addWidget(self.model_panel)
        layout.addWidget(self.excel_panel)
        layout.addWidget(self.action_panel)
        layout.addWidget(self.result_table, stretch=1)

        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------
    # Public API expected by MainController
    # ------------------------------------------------------------------

    def show_status(self, level: str, message: str) -> None:  # noqa: ARG002
        self.statusBar().showMessage(message)

    def set_busy(self, busy: bool, message: str | None = None) -> None:
        if busy:
            if self._busy_count == 0:
                self.model_panel.set_busy(True)
                self.excel_panel.set_busy(True)
                self.action_panel.set_busy(True)
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self._busy_count += 1
        elif self._busy_count > 0:
            self._busy_count -= 1
            if self._busy_count == 0:
                self.model_panel.set_busy(False)
                self.excel_panel.set_busy(False)
                self.action_panel.set_busy(False)
                QApplication.restoreOverrideCursor()

        if message:
            self.statusBar().showMessage(message)
        QApplication.processEvents()
