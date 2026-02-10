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


class ResultTable(QGroupBox):
    HEADERS = ["Row", "Input", "Prediction", "Score", "Status"]

    def __init__(self) -> None:
        super().__init__("Detection Results")
        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

    def clear_results(self) -> None:
        self.table.setRowCount(0)

    def set_results(self, results: list[DetectRowResult]) -> None:
        self.table.setRowCount(0)
        for row_index, result in enumerate(results):
            self.table.insertRow(row_index)
            for col_index, value in enumerate(result.to_table_row()):
                self.table.setItem(row_index, col_index, QTableWidgetItem(value))
