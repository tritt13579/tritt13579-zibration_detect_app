from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.domain.entities import DetectRowResult


_HEADERS = ["#", "Input", "Prediction", "Score", "Status"]


class ResultTable(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("Detection Results", parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 12, 8, 8)
        root.setSpacing(4)

        self._table = QTableWidget(0, len(_HEADERS))
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        root.addWidget(self._table)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clear_results(self) -> None:
        self._table.setRowCount(0)

    def set_results(self, results: list[DetectRowResult]) -> None:
        self._table.setRowCount(0)
        for result in results:
            row_data = result.to_table_row()
            row_idx = self._table.rowCount()
            self._table.insertRow(row_idx)
            for col, value in enumerate(row_data):
                self._table.setItem(row_idx, col, QTableWidgetItem(str(value)))
