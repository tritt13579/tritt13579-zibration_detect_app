from __future__ import annotations

from pathlib import Path

from app.domain.entities import AppState
from app.infrastructure.persistence.json_store import JsonStore


class AppStateRepository:
    def __init__(self, state_path: Path, json_store: JsonStore | None = None) -> None:
        self._state_path = state_path
        self._json_store = json_store or JsonStore()

    def load(self) -> AppState:
        payload = self._json_store.read_json(self._state_path, self._default_payload())
        payload["version"] = 1
        return AppState.from_dict(payload)

    def save(self, state: AppState) -> None:
        payload = state.to_dict()
        payload["version"] = 1
        self._json_store.write_json(self._state_path, payload)

    @staticmethod
    def _default_payload() -> dict:
        return {
            "last_used_model_id": None,
            "last_excel_path": None,
            "last_opened_at": None,
            "version": 1,
        }
