from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.application.controllers.main_controller import MainController
from app.application.services.detect_service import DetectService
from app.application.services.model_service import ModelService
from app.config.paths import (
    APP_STATE_PATH,
    MODEL_REGISTRY_PATH,
    MODELS_DIR,
    ensure_project_dirs,
)
from app.config.settings import AppSettings
from app.infrastructure.gateways.detector_gateway import DetectorGateway
from app.infrastructure.gateways.excel_gateway import ExcelGateway
from app.infrastructure.persistence.json_store import JsonStore
from app.infrastructure.repositories.app_state_repository import AppStateRepository
from app.infrastructure.repositories.model_repository import ModelRepository
from app.ui.main_window import MainWindow


DEFAULT_MODEL_REGISTRY = {"models": [], "version": 1}
DEFAULT_APP_STATE = {
    "last_used_model_id": None,
    "last_excel_path": None,
    "last_opened_at": None,
    "version": 1,
}


def build_application() -> tuple[QApplication, MainWindow, MainController]:
    ensure_project_dirs()
    _ensure_default_state_files()

    app = QApplication.instance() or QApplication(sys.argv)
    settings = AppSettings()

    json_store = JsonStore()
    model_repository = ModelRepository(
        registry_path=MODEL_REGISTRY_PATH,
        models_dir=MODELS_DIR,
        json_store=json_store,
    )
    app_state_repository = AppStateRepository(state_path=APP_STATE_PATH, json_store=json_store)

    model_service = ModelService(model_repository, app_state_repository)
    detect_service = DetectService(
        excel_gateway=ExcelGateway(),
        detector_gateway=DetectorGateway(),
        app_state_repository=app_state_repository,
    )

    window = MainWindow(settings=settings)
    controller = MainController(window, model_service, detect_service)
    controller.initialize()

    return app, window, controller



def _ensure_default_state_files() -> None:
    json_store = JsonStore()
    if not MODEL_REGISTRY_PATH.exists():
        json_store.write_json(MODEL_REGISTRY_PATH, DEFAULT_MODEL_REGISTRY)
    if not APP_STATE_PATH.exists():
        json_store.write_json(APP_STATE_PATH, DEFAULT_APP_STATE)
