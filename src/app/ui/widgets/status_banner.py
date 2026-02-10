from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout


class StatusBanner(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("StatusBanner")
        self.setProperty("statusLevel", "info")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)

        self._label = QLabel("Ready")
        self._label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._label.setObjectName("StatusBannerLabel")
        layout.addWidget(self._label)

    def set_status(self, level: str, message: str) -> None:
        self.setProperty("statusLevel", level)
        self._label.setText(message)
        self.style().unpolish(self)
        self.style().polish(self)
