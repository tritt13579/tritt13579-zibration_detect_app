from pathlib import Path

import pytest

from app.infrastructure.repositories.model_repository import ModelRepository


def test_add_model_and_query(tmp_path: Path) -> None:
    registry_path = tmp_path / "state" / "model_registry.json"
    models_dir = tmp_path / "models"
    repo = ModelRepository(registry_path=registry_path, models_dir=models_dir)

    source_model = tmp_path / "my_model.pt"
    source_model.write_bytes(b"mock-pt")

    record = repo.add_model(str(source_model))

    assert Path(record.stored_path).exists()
    assert Path(record.stored_path).parent == models_dir

    all_models = repo.list_models()
    assert len(all_models) == 1
    assert all_models[0].id == record.id

    found = repo.get_model(record.id)
    assert found is not None
    assert found.original_name == "my_model.pt"


def test_add_model_rejects_non_pt(tmp_path: Path) -> None:
    repo = ModelRepository(
        registry_path=tmp_path / "state" / "model_registry.json",
        models_dir=tmp_path / "models",
    )
    bad_file = tmp_path / "wrong.txt"
    bad_file.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError):
        repo.add_model(str(bad_file))
