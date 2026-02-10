from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout


class ExcelPanel(QGroupBox):
    browse_requested = Signal()
    load_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Step 2 - Excel")
        self.setObjectName("Card")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(8)

        self.path_edit = QLineEdit()
        self.path_edit.setObjectName("PathInput")
        self.path_edit.setPlaceholderText("Choose an Excel file (.xlsx or .xls)")
        self.path_edit.setReadOnly(True)
        row.addWidget(self.path_edit, stretch=1)

        self.browse_button = QPushButton("Browse")
        self.browse_button.setObjectName("GhostButton")
        self.browse_button.clicked.connect(self.browse_requested.emit)
        row.addWidget(self.browse_button)

        self.load_button = QPushButton("Load")
        self.load_button.setObjectName("PrimaryButton")
        self.load_button.clicked.connect(self.load_requested.emit)
        row.addWidget(self.load_button)

        root_layout.addLayout(row)

    def set_path(self, path: str) -> None:
        self.path_edit.setText(path)

    def path(self) -> str:
        return self.path_edit.text()
