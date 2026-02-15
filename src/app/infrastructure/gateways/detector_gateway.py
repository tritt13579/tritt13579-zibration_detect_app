from __future__ import annotations

from pathlib import Path

from app.domain.entities import DetectRowResult, ModelRecord


class DetectorGateway:
    """Gateway for running vibration detection inference."""

    def detect(self, model: ModelRecord, rows: list[dict]) -> list[DetectRowResult]:
        """Run detection on Excel data rows.
        
        Note: The 'rows' parameter is legacy from mock implementation.
        We now expect the Excel DataFrame to be loaded separately.
        This method will be called from DetectService with proper data.
        """
        # This is a placeholder - actual detection happens in detect_from_excel
        results: list[DetectRowResult] = []
        for index, row in enumerate(rows, start=1):
            input_preview = str(row.get("input", ""))
            results.append(
                DetectRowResult(
                    row_index=index,
                    input_preview=input_preview,
                    prediction="N/A (use detect_from_excel)",
                    score=0.0,
                    status="pending",
                )
            )
        return results

    def detect_from_excel(
        self,
        model: ModelRecord,
        excel_df,
        excel_filename: str = "data",
    ) -> list[DetectRowResult]:
        """Run real detection on Excel DataFrame.
        
        Args:
            model: Model record with path to .pt file
            excel_df: pandas DataFrame with vibration data
            excel_filename: Name of Excel file for display purposes
            
        Returns:
            List of detection results, one per window
            
        Raises:
            FileNotFoundError: If model file not found
            ValueError: If model checkpoint is invalid or data preprocessing fails
        """
        # Lazy import to avoid loading torch/pandas at app startup
        # This prevents conflicts with PySide6
        import numpy as np
        import torch
        
        from app.infrastructure.models import SimpleCNN1D
        from app.infrastructure.preprocessing import preprocess_excel_for_inference
        
        model_path = Path(model.stored_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model.stored_path}")

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        checkpoint = torch.load(model_path, map_location=device, weights_only=False)

        classes = checkpoint.get("classes", [])
        cfg = checkpoint.get("cfg", {})
        cnn1d_params = checkpoint.get("cnn1d_params", {})
        meta = checkpoint.get("meta", {})

        channels = cfg.get("channels", 3)
        window = cfg.get("window", 2048)
        step = cfg.get("step", 2048)
        eps = cfg.get("eps", 1e-8)

        mean = meta.get("mean")
        std = meta.get("std")

        if mean is None or std is None:
            raise ValueError("Model checkpoint missing normalization parameters (mean/std)")

        mean = np.array(mean, dtype=np.float32)
        std = np.array(std, dtype=np.float32)

        base_filters = cnn1d_params.get("base_filters", 64)
        dropout = cnn1d_params.get("dropout", 0.4)

        cnn_model = SimpleCNN1D(
            num_classes=len(classes),
            input_channels=channels,
            base_filters=base_filters,
            dropout=dropout,
        ).to(device)

        cnn_model.load_state_dict(checkpoint["model_state_dict"])
        cnn_model.eval()

        batch, num_windows = preprocess_excel_for_inference(
            df=excel_df,
            window=window,
            step=step,
            mean=mean,
            std=std,
            channels=channels,
            eps=eps,
        )

        batch = batch.to(device)

        with torch.no_grad():
            logits = cnn_model(batch)
            probs = torch.softmax(logits, dim=1)
            scores, predictions = torch.max(probs, dim=1)

        predictions = predictions.cpu().numpy()
        scores = scores.cpu().numpy()

        results: list[DetectRowResult] = []
        for idx in range(num_windows):
            pred_class_idx = int(predictions[idx])
            confidence = float(scores[idx])

            class_name = classes[pred_class_idx] if pred_class_idx < len(classes) else f"Class_{pred_class_idx}"

            status = "high_confidence" if confidence > 0.8 else "review"

            results.append(
                DetectRowResult(
                    row_index=idx + 1,
                    input_preview=f"{excel_filename} (window {idx + 1}/{num_windows})",
                    prediction=class_name,
                    score=confidence,
                    status=status,
                )
            )

        return results

