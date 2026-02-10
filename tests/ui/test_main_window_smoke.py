from pathlib import Path

from PySide6.QtCore import Qt

from app.application.controllers.main_controller import MainController
from app.application.services.detect_service import DetectService
from app.application.services.model_service import ModelService
from app.config.settings import AppSettings
from app.infrastructure.gateways.detector_gateway import DetectorGateway
from app.infrastructure.gateways.excel_gateway import ExcelGateway
from app.infrastructure.persistence.json_store import JsonStore
from app.infrastructure.repositories.app_state_repository import AppStateRepository
from app.infrastructure.repositories.model_repository import ModelRepository
from app.ui.main_window import MainWindow


def _seed_state_files(json_store: JsonStore, registry_path: Path, app_state_path: Path) -> None:
    json_store.write_json(registry_path, {"models": [], "version": 1})
    json_store.write_json(
        app_state_path,
        {
            "last_used_model_id": None,
            "last_excel_path": None,
            "last_opened_at": None,
            "version": 1,
        },
    )


def test_main_window_smoke(qtbot, tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    state_dir = tmp_path / "state"
    registry_path = state_dir / "model_registry.json"
    app_state_path = state_dir / "app_state.json"

    json_store = JsonStore()
    _seed_state_files(json_store, registry_path, app_state_path)

    model_repository = ModelRepository(
        registry_path=registry_path,
        models_dir=models_dir,
        json_store=json_store,
    )
    app_state_repository = AppStateRepository(state_path=app_state_path, json_store=json_store)
    model_service = ModelService(model_repository, app_state_repository)
    detect_service = DetectService(
        excel_gateway=ExcelGateway(),
        detector_gateway=DetectorGateway(),
        app_state_repository=app_state_repository,
    )

    source_model = tmp_path / "demo.pt"
    source_model.write_bytes(b"model")
    imported_model = model_service.import_model(str(source_model))

    window = MainWindow(AppSettings())
    controller = MainController(window, model_service, detect_service)
    controller.initialize()

    qtbot.addWidget(window)
    window.show()

    assert window.model_panel.selected_model_id() == imported_model.id

    excel_file = tmp_path / "input.xlsx"
    excel_file.write_text("dummy", encoding="utf-8")
    window.excel_panel.set_path(str(excel_file))

    qtbot.mouseClick(window.excel_panel.load_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(window.action_panel.run_button, Qt.MouseButton.LeftButton)

    assert window.result_table.table.rowCount() > 0
