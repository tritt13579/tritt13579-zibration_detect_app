from __future__ import annotations

from pathlib import Path


class ExcelGateway:
    SUPPORTED_EXTENSIONS = {".xlsx", ".xls"}

    def validate_excel_path(self, path: str) -> None:
        excel_path = Path(path)
        if not excel_path.exists() or not excel_path.is_file():
            raise FileNotFoundError(f"Excel file not found: {path}")
        if excel_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("Only .xlsx and .xls files are supported.")

    def read_preview(self, path: str) -> list[dict]:
        self.validate_excel_path(path)
        stem = Path(path).stem
        return [{"input": f"{stem}_sample_{idx:02d}"} for idx in range(1, 21)]
