from __future__ import annotations

from pathlib import Path

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
        self._loaded_excel_df = None
        self._loaded_excel_path: str | None = None

    def load_excel_preview(self, path: str) -> list[dict]:
        """Load Excel file and store DataFrame for later detection.
        
        Returns preview information for display.
        """
        self._excel_gateway.validate_excel_path(path)
        
        # Load the actual DataFrame and store it for detection
        self._loaded_excel_df = self._excel_gateway.read_excel_data(path)
        self._loaded_excel_path = path
        
        # Get preview rows for compatibility with UI
        rows = self._excel_gateway.read_preview(path)

        state = self._app_state_repository.load()
        state.last_excel_path = path
        self._app_state_repository.save(state)
        return rows

    def get_last_excel_path(self) -> str | None:
        return self._app_state_repository.load().last_excel_path

    def run_detect(self, model: ModelRecord, rows: list[dict]) -> list[DetectRowResult]:
        """Run detection using stored Excel DataFrame.
        
        Args:
            model: Model record with path to trained model
            rows: Legacy parameter, not used (kept for compatibility)
            
        Returns:
            Detection results for each window in the Excel data
            
        Raises:
            ValueError: If no Excel data has been loaded
        """
        if self._loaded_excel_df is None:
            raise ValueError("No Excel data loaded. Please load an Excel file first.")
        
        # Get filename for display
        excel_filename = "data"
        if self._loaded_excel_path:
            excel_filename = Path(self._loaded_excel_path).stem
        
        # Use the new detect_from_excel method
        return self._detector_gateway.detect_from_excel(
            model=model,
            excel_df=self._loaded_excel_df,
            excel_filename=excel_filename,
        )

