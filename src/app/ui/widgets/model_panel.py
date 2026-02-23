from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.domain.entities import ModelRecord


class ModelPanel(QGroupBox):
    add_model_requested = Signal()
    model_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__("Model", parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 12, 8, 8)
        root.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(6)

        self._combo = QComboBox()
        self._combo.setMinimumWidth(200)
        self._combo.addItem("Select saved model...")
        row.addWidget(self._combo, stretch=1)

        self._add_btn = QPushButton("Add Model (.pt)")
        row.addWidget(self._add_btn)

        root.addLayout(row)

        self._active_label = QLabel("No model selected")
        root.addWidget(self._active_label)

        # wiring
        self._add_btn.clicked.connect(self.add_model_requested)
        self._combo.currentIndexChanged.connect(self._on_index_changed)

        self._model_ids: list[str] = []

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_index_changed(self, index: int) -> None:
        if index <= 0:
            self.model_changed.emit("")
        else:
            self.model_changed.emit(self._model_ids[index - 1])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_models(self, models: list[ModelRecord], selected_model_id: str | None) -> None:
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem("Select saved model...")
        self._model_ids = [m.id for m in models]
        for model in models:
            self._combo.addItem(model.display_name)
        if selected_model_id:
            try:
                idx = self._model_ids.index(selected_model_id) + 1
                self._combo.setCurrentIndex(idx)
            except ValueError:
                self._combo.setCurrentIndex(0)
        else:
            self._combo.setCurrentIndex(0)
        self._combo.blockSignals(False)

    def selected_model_id(self) -> str:
        idx = self._combo.currentIndex()
        if idx <= 0:
            return ""
        return self._model_ids[idx - 1]

    def set_active_model_text(self, label: str) -> None:
        self._active_label.setText(label)
