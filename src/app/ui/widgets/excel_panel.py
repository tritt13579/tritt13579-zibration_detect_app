from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class ExcelPanel(QGroupBox):
    browse_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__("Excel File", parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 12, 8, 8)
        root.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(6)

        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("No file selected")
        self._path_edit.setReadOnly(True)
        row.addWidget(self._path_edit, stretch=1)

        self._browse_btn = QPushButton("Browse...")
        row.addWidget(self._browse_btn)

        root.addLayout(row)

        self._browse_btn.clicked.connect(self.browse_requested)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_path(self, path: str) -> None:
        self._path_edit.setText(path)
        self._path_edit.setToolTip(path)

    def path(self) -> str:
        return self._path_edit.text()

    def set_busy(self, busy: bool) -> None:
        self._browse_btn.setEnabled(not busy)
        self._browse_btn.setText("Loading..." if busy else "Browse...")
