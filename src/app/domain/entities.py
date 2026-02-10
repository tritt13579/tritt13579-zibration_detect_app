from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ModelRecord:
    id: str
    display_name: str
    stored_path: str
    original_name: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "stored_path": self.stored_path,
            "original_name": self.original_name,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ModelRecord":
        return cls(
            id=str(payload.get("id", "")),
            display_name=str(payload.get("display_name", "")),
            stored_path=str(payload.get("stored_path", "")),
            original_name=str(payload.get("original_name", "")),
            created_at=str(payload.get("created_at", "")),
        )


@dataclass(slots=True)
class AppState:
    last_used_model_id: str | None = None
    last_excel_path: str | None = None
    last_opened_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_used_model_id": self.last_used_model_id,
            "last_excel_path": self.last_excel_path,
            "last_opened_at": self.last_opened_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AppState":
        return cls(
            last_used_model_id=payload.get("last_used_model_id"),
            last_excel_path=payload.get("last_excel_path"),
            last_opened_at=payload.get("last_opened_at"),
        )


@dataclass(slots=True)
class DetectRowResult:
    row_index: int
    input_preview: str
    prediction: str
    score: float
    status: str

    def to_table_row(self) -> list[str]:
        return [
            str(self.row_index),
            self.input_preview,
            self.prediction,
            f"{self.score:.3f}",
            self.status,
        ]
