from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from app.config.settings import AppSettings
from app.ui.widgets.action_panel import ActionPanel
from app.ui.widgets.excel_panel import ExcelPanel
from app.ui.widgets.model_panel import ModelPanel
from app.ui.widgets.result_table import ResultTable
from app.ui.widgets.status_banner import StatusBanner


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.setWindowTitle(settings.app_name)
        self.resize(settings.window_width, settings.window_height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(22, 20, 22, 20)
        root_layout.setSpacing(14)

        self.status_banner = StatusBanner()
        root_layout.addWidget(self.status_banner)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        self.model_panel = ModelPanel()
        top_row.addWidget(self.model_panel, stretch=3)

        self.excel_panel = ExcelPanel()
        top_row.addWidget(self.excel_panel, stretch=4)

        root_layout.addLayout(top_row)

        self.action_panel = ActionPanel()
        root_layout.addWidget(self.action_panel)

        self.result_table = ResultTable()
        root_layout.addWidget(self.result_table, stretch=1)

    def show_status(self, level: str, message: str) -> None:
        self.status_banner.set_status(level, message)
