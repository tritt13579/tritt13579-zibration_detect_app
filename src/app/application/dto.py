from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities import ModelRecord


@dataclass(slots=True)
class StartupData:
    models: list[ModelRecord]
    selected_model_id: str | None
    last_excel_path: str | None
