from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
)


class ActionPanel(QGroupBox):
    run_detect_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__("Detect", parent)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 12, 8, 8)
        row.setSpacing(12)

        self._hint = QLabel("Select a model and an Excel file, then click Run Detect.")
        row.addWidget(self._hint, stretch=1)

        self._run_btn = QPushButton("Run Detect")
        row.addWidget(self._run_btn)

        self._run_btn.clicked.connect(self.run_detect_requested)

    def set_busy(self, busy: bool) -> None:
        self._run_btn.setEnabled(not busy)
        self._run_btn.setText("Detecting..." if busy else "Run Detect")
