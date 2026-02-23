from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog

from app.application.services.detect_service import DetectService
from app.application.services.model_service import ModelService
from app.ui.main_window import MainWindow


class MainController:
    def __init__(
        self,
        window: MainWindow,
        model_service: ModelService,
        detect_service: DetectService,
    ) -> None:
        self._window = window
        self._model_service = model_service
        self._detect_service = detect_service
        self._preview_rows: list[dict] = []

        self._window.model_panel.add_model_requested.connect(self._on_add_model)
        self._window.model_panel.model_changed.connect(self._on_model_changed)
        self._window.excel_panel.browse_requested.connect(self._on_browse_excel)
        self._window.action_panel.run_detect_requested.connect(self._on_run_detect)

    def initialize(self) -> None:
        self._model_service.mark_opened()
        self._refresh_models()

        last_excel_path = self._detect_service.get_last_excel_path()
        if last_excel_path:
            self._window.excel_panel.set_path(last_excel_path)

        if not self._model_service.list_models():
            self._window.show_status(
                "info",
                "Start by adding a .pt model file.",
            )
        else:
            self._window.show_status(
                "success",
                "Ready. Choose an Excel file to auto-load and run detect.",
            )

    def _refresh_models(self, preferred_model_id: str | None = None) -> None:
        models = self._model_service.list_models()
        selected_id = preferred_model_id or self._model_service.get_recent_model_id()
        self._window.model_panel.set_models(models, selected_id)

        if selected_id:
            model = self._model_service.get_model(selected_id)
            if model:
                self._window.model_panel.set_active_model_text(model.display_name)
                return
        self._window.model_panel.set_active_model_text("No model selected")

    def _on_add_model(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self._window,
            "Choose .pt model",
            "",
            "PyTorch Model (*.pt)",
        )
        if not file_path:
            return

        try:
            model = self._model_service.import_model(file_path)
            self._refresh_models(model.id)
            self._window.show_status("success", f"Model imported: {Path(file_path).name}")
        except Exception as exc:  # noqa: BLE001
            self._window.show_status("error", str(exc))

    def _on_model_changed(self, model_id: str) -> None:
        if not model_id:
            self._model_service.set_active_model(None)
            self._window.model_panel.set_active_model_text("No model selected")
            return

        model = self._model_service.get_model(model_id)
        if model is None:
            self._window.show_status("error", "Selected model does not exist.")
            self._window.model_panel.set_active_model_text("No model selected")
            return

        self._model_service.set_active_model(model.id)
        self._window.model_panel.set_active_model_text(model.display_name)

    def _on_browse_excel(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self._window,
            "Choose Excel file",
            "",
            "Excel Files (*.xlsx *.xls)",
        )
        if not file_path:
            return
        self._window.excel_panel.set_path(file_path)
        self._load_excel_from_path(file_path)

    def _load_excel_from_path(self, path: str) -> None:
        """Load selected Excel into memory for detection."""

        try:
            self._preview_rows = self._detect_service.load_excel_preview(path)
            self._window.result_table.clear_results()
            self._window.show_status(
                "success",
                "Excel loaded and ready for detect.",
            )
        except Exception as exc:  # noqa: BLE001
            self._window.show_status("error", str(exc))

    def _on_run_detect(self) -> None:
        model_id = self._window.model_panel.selected_model_id()
        if not model_id:
            self._window.show_status("warning", "Please select a model before running detect.")
            return

        if not self._preview_rows:
            self._window.show_status("warning", "Please choose an Excel file before running detect.")
            return

        model = self._model_service.get_model(model_id)
        if not model:
            self._window.show_status("error", "Selected model is unavailable.")
            return

        try:
            results = self._detect_service.run_detect(model, self._preview_rows)
            self._window.result_table.set_results(results)
            self._window.show_status("success", "Detect completed: 1 aggregated file-level result.")
        except Exception as exc:  # noqa: BLE001
            self._window.show_status("error", str(exc))
