from __future__ import annotations

from app.domain.entities import DetectRowResult, ModelRecord
from app.domain.protocols import IAppStateRepository, IDetectorGateway, IExcelGateway


class DetectService:
    def __init__(
        self,
        excel_gateway: IExcelGateway,
        detector_gateway: IDetectorGateway,
        app_state_repository: IAppStateRepository,
    ) -> None:
        self._excel_gateway = excel_gateway
        self._detector_gateway = detector_gateway
        self._app_state_repository = app_state_repository

    def load_excel_preview(self, path: str) -> list[dict]:
        self._excel_gateway.validate_excel_path(path)
        rows = self._excel_gateway.read_preview(path)

        state = self._app_state_repository.load()
        state.last_excel_path = path
        self._app_state_repository.save(state)
        return rows

    def get_last_excel_path(self) -> str | None:
        return self._app_state_repository.load().last_excel_path

    def run_detect(self, model: ModelRecord, rows: list[dict]) -> list[DetectRowResult]:
        if not rows:
            raise ValueError("No input rows loaded.")
        return self._detector_gateway.detect(model, rows)
