from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from shutil import copy2
from uuid import uuid4

from app.domain.entities import ModelRecord
from app.infrastructure.persistence.json_store import JsonStore


class ModelRepository:
    def __init__(
        self,
        registry_path: Path,
        models_dir: Path,
        json_store: JsonStore | None = None,
    ) -> None:
        self._registry_path = registry_path
        self._models_dir = models_dir
        self._json_store = json_store or JsonStore()

    def add_model(self, source_pt_path: str) -> ModelRecord:
        source_path = Path(source_pt_path)
        if not source_path.exists() or not source_path.is_file():
            raise FileNotFoundError(f"Model file not found: {source_pt_path}")
        if source_path.suffix.lower() != ".pt":
            raise ValueError("Only .pt model files are supported.")

        self._models_dir.mkdir(parents=True, exist_ok=True)
        created_at = datetime.now(UTC).isoformat()
        model_id = str(uuid4())
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        slug = self._slugify(source_path.stem)
        target_name = f"{timestamp}_{slug}.pt"
        target_path = self._models_dir / target_name
        if target_path.exists():
            target_path = self._models_dir / f"{timestamp}_{slug}_{model_id[:8]}.pt"

        copy2(source_path, target_path)

        display_name = f"{source_path.stem} ({timestamp})"
        record = ModelRecord(
            id=model_id,
            display_name=display_name,
            stored_path=str(target_path.resolve()),
            original_name=source_path.name,
            created_at=created_at,
        )

        registry = self._load_registry()
        registry["models"].append(record.to_dict())
        self._save_registry(registry)

        return record

    def list_models(self) -> list[ModelRecord]:
        registry = self._load_registry()
        records: list[ModelRecord] = [
            ModelRecord.from_dict(model_payload)
            for model_payload in registry.get("models", [])
            if isinstance(model_payload, dict)
        ]
        return sorted(records, key=lambda item: item.created_at, reverse=True)

    def get_model(self, model_id: str) -> ModelRecord | None:
        for model in self.list_models():
            if model.id == model_id:
                return model
        return None

    def _load_registry(self) -> dict:
        default_registry = {"models": [], "version": 1}
        data = self._json_store.read_json(self._registry_path, default_registry)
        if "models" not in data or not isinstance(data["models"], list):
            data["models"] = []
        data["version"] = 1
        return data

    def _save_registry(self, data: dict) -> None:
        self._json_store.write_json(self._registry_path, data)

    @staticmethod
    def _slugify(raw_name: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", raw_name).strip("_")
        return normalized.lower() or "model"
