from __future__ import annotations

from datetime import UTC, datetime

from app.domain.entities import AppState, ModelRecord
from app.domain.protocols import IAppStateRepository, IModelRepository


class ModelService:
    def __init__(
        self,
        model_repository: IModelRepository,
        app_state_repository: IAppStateRepository,
    ) -> None:
        self._model_repository = model_repository
        self._app_state_repository = app_state_repository

    def list_models(self) -> list[ModelRecord]:
        return self._model_repository.list_models()

    def get_model(self, model_id: str) -> ModelRecord | None:
        return self._model_repository.get_model(model_id)

    def import_model(self, source_pt_path: str) -> ModelRecord:
        model = self._model_repository.add_model(source_pt_path)
        self.set_active_model(model.id)
        return model

    def get_recent_model_id(self) -> str | None:
        state = self._app_state_repository.load()
        recent_id = state.last_used_model_id
        if not recent_id:
            return None
        if self._model_repository.get_model(recent_id) is None:
            return None
        return recent_id

    def set_active_model(self, model_id: str | None) -> None:
        state = self._app_state_repository.load()
        state.last_used_model_id = model_id
        state.last_opened_at = _utc_now()
        self._app_state_repository.save(state)

    def mark_opened(self) -> AppState:
        state = self._app_state_repository.load()
        state.last_opened_at = _utc_now()
        self._app_state_repository.save(state)
        return state



def _utc_now() -> str:
    return datetime.now(UTC).isoformat()
