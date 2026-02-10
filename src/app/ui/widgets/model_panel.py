from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.domain.entities import ModelRecord


class ModelPanel(QGroupBox):
    add_model_requested = Signal()
    model_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__("Step 1 - Model")
        self.setObjectName("Card")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(8)

        self.model_combo = QComboBox()
        self.model_combo.setObjectName("PrimaryCombo")
        self.model_combo.currentIndexChanged.connect(self._emit_model_changed)
        row.addWidget(self.model_combo, stretch=1)

        self.add_button = QPushButton("Add Model (.pt)")
        self.add_button.setObjectName("PrimaryButton")
        self.add_button.clicked.connect(self.add_model_requested.emit)
        row.addWidget(self.add_button)

        root_layout.addLayout(row)

        self.active_label = QLabel("Active: No model selected")
        self.active_label.setObjectName("SubtleLabel")
        root_layout.addWidget(self.active_label)

    def set_models(self, models: list[ModelRecord], selected_model_id: str | None) -> None:
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        self.model_combo.addItem("Select saved model...", "")
        for model in models:
            self.model_combo.addItem(model.display_name, model.id)

        target_index = 0
        if selected_model_id:
            found_index = self.model_combo.findData(selected_model_id)
            if found_index >= 0:
                target_index = found_index

        self.model_combo.setCurrentIndex(target_index)
        self.model_combo.blockSignals(False)

        current_model_id = self.selected_model_id()
        if current_model_id:
            self.model_changed.emit(current_model_id)

    def selected_model_id(self) -> str | None:
        data = self.model_combo.currentData()
        if not data:
            return None
        return str(data)

    def set_active_model_text(self, label: str) -> None:
        self.active_label.setText(f"Active: {label}")

    def _emit_model_changed(self, _: int) -> None:
        model_id = self.selected_model_id()
        self.model_changed.emit(model_id or "")
