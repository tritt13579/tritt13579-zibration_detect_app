from __future__ import annotations

from typing import Protocol

from app.domain.entities import AppState, DetectRowResult, ModelRecord


class IModelRepository(Protocol):
    def add_model(self, source_pt_path: str) -> ModelRecord:
        ...

    def list_models(self) -> list[ModelRecord]:
        ...

    def get_model(self, model_id: str) -> ModelRecord | None:
        ...


class IAppStateRepository(Protocol):
    def load(self) -> AppState:
        ...

    def save(self, state: AppState) -> None:
        ...


class IExcelGateway(Protocol):
    def validate_excel_path(self, path: str) -> None:
        ...

    def read_preview(self, path: str) -> list[dict]:
        ...


class IDetectorGateway(Protocol):
    def detect(self, model: ModelRecord, rows: list[dict]) -> list[DetectRowResult]:
        ...
