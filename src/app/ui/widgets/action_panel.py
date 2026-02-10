from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton


class ActionPanel(QGroupBox):
    run_detect_requested = Signal()

    def __init__(self) -> None:
        super().__init__("Step 3 - Detect")
        self.setObjectName("Card")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        hint = QLabel("After loading Excel rows, click run detect.")
        hint.setObjectName("SubtleLabel")
        layout.addWidget(hint, stretch=1)

        self.run_button = QPushButton("Run Detect")
        self.run_button.setObjectName("PrimaryButton")
        self.run_button.clicked.connect(self.run_detect_requested.emit)
        layout.addWidget(self.run_button)
