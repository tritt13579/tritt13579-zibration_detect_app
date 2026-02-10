from pathlib import Path

from app.domain.entities import AppState
from app.infrastructure.repositories.app_state_repository import AppStateRepository


def test_load_default_and_save(tmp_path: Path) -> None:
    state_path = tmp_path / "state" / "app_state.json"
    repo = AppStateRepository(state_path=state_path)

    initial_state = repo.load()
    assert initial_state.last_used_model_id is None
    assert initial_state.last_excel_path is None

    repo.save(
        AppState(
            last_used_model_id="model-123",
            last_excel_path="/tmp/a.xlsx",
            last_opened_at="2026-02-10T00:00:00+00:00",
        )
    )

    loaded_state = repo.load()
    assert loaded_state.last_used_model_id == "model-123"
    assert loaded_state.last_excel_path == "/tmp/a.xlsx"
