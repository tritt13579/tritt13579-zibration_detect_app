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

    def read_excel_data(self, path: str):
        """Read Excel file and return DataFrame.
        
        Args:
            path: Path to Excel file
            
        Returns:
            DataFrame with all data from Excel
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        # Lazy import pandas to avoid conflicts with PySide6
        import pandas as pd
        
        self.validate_excel_path(path)
        return pd.read_excel(path, engine="openpyxl")

    def read_preview(self, path: str) -> list[dict]:
        """Read Excel file for preview (legacy method for compatibility).
        
        Returns basic info about the file rather than actual data rows.
        The actual detection process uses read_excel_data() instead.
        """
        self.validate_excel_path(path)
        df = self.read_excel_data(path)
        stem = Path(path).stem
        
        return [
            {
                "input": f"{stem} ({df.shape[0]} rows × {df.shape[1]} cols)",
                "columns": str(df.columns.tolist()[:5]),
            }
        ]


