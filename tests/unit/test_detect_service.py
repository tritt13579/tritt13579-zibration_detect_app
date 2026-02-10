from pathlib import Path

from app.application.services.detect_service import DetectService
from app.domain.entities import ModelRecord
from app.infrastructure.gateways.detector_gateway import DetectorGateway
from app.infrastructure.gateways.excel_gateway import ExcelGateway
from app.infrastructure.repositories.app_state_repository import AppStateRepository


def test_detect_service_loads_preview_and_detects(tmp_path: Path) -> None:
    state_repo = AppStateRepository(state_path=tmp_path / "state" / "app_state.json")
    service = DetectService(
        excel_gateway=ExcelGateway(),
        detector_gateway=DetectorGateway(),
        app_state_repository=state_repo,
    )

    excel_file = tmp_path / "sample.xlsx"
    excel_file.write_text("placeholder", encoding="utf-8")

    rows = service.load_excel_preview(str(excel_file))
    assert len(rows) == 20
    assert service.get_last_excel_path() == str(excel_file)

    model = ModelRecord(
        id="model-a",
        display_name="Model A",
        stored_path=str(tmp_path / "stored.pt"),
        original_name="stored.pt",
        created_at="2026-02-10T00:00:00+00:00",
    )
    results = service.run_detect(model, rows)

    assert len(results) == len(rows)
    assert results[0].row_index == 1
    assert results[0].prediction in {"Normal", "Anomaly"}
