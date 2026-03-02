from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.domain.entities import DetectReport, DetectRowResult


_CLASS_HEADERS = ["Rank", "Class", "Probability"]
_WINDOW_HEADERS = ["Window", "Sample Range", "Prediction", "Score", "Status"]


class ResultTable(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("Detection Results", parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 12, 8, 8)
        root.setSpacing(8)

        summary_group = QGroupBox("Run Summary")
        summary_layout = QGridLayout(summary_group)
        summary_layout.setContentsMargins(8, 8, 8, 8)
        summary_layout.setHorizontalSpacing(16)
        summary_layout.setVerticalSpacing(4)

        self._summary_values: dict[str, QLabel] = {}
        summary_fields = [
            ("File", "file"),
            ("Model", "model"),
            ("Final Prediction", "prediction"),
            ("Confidence", "confidence"),
            ("Status", "status"),
            ("Windows", "windows"),
            ("Window/Step", "window_step"),
            ("Run Time", "runtime"),
            ("Generated At", "generated_at"),
        ]
        for index, (title, key) in enumerate(summary_fields):
            row = index // 3
            column = (index % 3) * 2
            key_label = QLabel(f"{title}:")
            value_label = QLabel("-")
            summary_layout.addWidget(key_label, row, column)
            summary_layout.addWidget(value_label, row, column + 1)
            self._summary_values[key] = value_label

        class_title = QLabel("Class Probabilities (mean over windows)")
        self._class_table = QTableWidget(0, len(_CLASS_HEADERS))
        self._class_table.setHorizontalHeaderLabels(_CLASS_HEADERS)
        self._class_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._class_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._class_table.setAlternatingRowColors(True)
        self._class_table.verticalHeader().setVisible(False)
        self._class_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._class_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._class_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        window_title = QLabel("Window-level Predictions")
        self._window_table = QTableWidget(0, len(_WINDOW_HEADERS))
        self._window_table.setHorizontalHeaderLabels(_WINDOW_HEADERS)
        self._window_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._window_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._window_table.setAlternatingRowColors(True)
        self._window_table.verticalHeader().setVisible(False)
        self._window_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._window_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._window_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._window_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._window_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        root.addWidget(summary_group)
        root.addWidget(class_title)
        root.addWidget(self._class_table)
        root.addWidget(window_title)
        root.addWidget(self._window_table, stretch=1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clear_results(self) -> None:
        for value in self._summary_values.values():
            value.setText("-")
        self._class_table.setRowCount(0)
        self._window_table.setRowCount(0)

    @property
    def table(self) -> QTableWidget:
        return self._window_table

    def set_report(self, report: DetectReport) -> None:
        self._summary_values["file"].setText(report.excel_filename)
        self._summary_values["model"].setText(report.model_name)
        self._summary_values["prediction"].setText(report.prediction)
        self._summary_values["confidence"].setText(f"{report.confidence * 100:.2f}%")
        self._summary_values["status"].setText(report.status)
        self._summary_values["windows"].setText(str(report.num_windows))
        self._summary_values["window_step"].setText(f"{report.window_size}/{report.step_size}")
        self._summary_values["runtime"].setText(f"{report.run_time_ms} ms")
        self._summary_values["generated_at"].setText(report.generated_at)

        self._class_table.setRowCount(0)
        for class_prob in report.class_probabilities:
            row_idx = self._class_table.rowCount()
            self._class_table.insertRow(row_idx)
            self._class_table.setItem(row_idx, 0, QTableWidgetItem(str(class_prob.rank)))
            self._class_table.setItem(row_idx, 1, QTableWidgetItem(class_prob.class_name))
            self._class_table.setItem(row_idx, 2, QTableWidgetItem(f"{class_prob.probability * 100:.2f}%"))

        self._window_table.setRowCount(0)
        for detection in report.window_detections:
            row_idx = self._window_table.rowCount()
            self._window_table.insertRow(row_idx)
            self._window_table.setItem(row_idx, 0, QTableWidgetItem(str(detection.window_index)))
            self._window_table.setItem(
                row_idx,
                1,
                QTableWidgetItem(f"{detection.sample_start}-{detection.sample_end}"),
            )
            self._window_table.setItem(row_idx, 2, QTableWidgetItem(detection.prediction))
            self._window_table.setItem(row_idx, 3, QTableWidgetItem(f"{detection.score * 100:.2f}%"))
            self._window_table.setItem(row_idx, 4, QTableWidgetItem(detection.status))

    def set_results(self, results: list[DetectRowResult]) -> None:
        self.clear_results()
        if not results:
            return

        first_row = results[0]
        self._summary_values["prediction"].setText(first_row.prediction)
        self._summary_values["confidence"].setText(f"{first_row.score * 100:.2f}%")
        self._summary_values["status"].setText(first_row.status)
        self._summary_values["windows"].setText(str(len(results)))

        for result in results:
            row_idx = self._window_table.rowCount()
            self._window_table.insertRow(row_idx)
            self._window_table.setItem(row_idx, 0, QTableWidgetItem(str(result.row_index)))
            self._window_table.setItem(row_idx, 1, QTableWidgetItem(result.input_preview))
            self._window_table.setItem(row_idx, 2, QTableWidgetItem(result.prediction))
            self._window_table.setItem(row_idx, 3, QTableWidgetItem(f"{result.score * 100:.2f}%"))
            self._window_table.setItem(row_idx, 4, QTableWidgetItem(result.status))
