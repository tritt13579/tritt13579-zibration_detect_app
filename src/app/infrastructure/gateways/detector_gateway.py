from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from app.domain.entities import (
    ClassProbability,
    DetectReport,
    ModelRecord,
    WindowDetection,
)


class DetectorGateway:
    """Gateway for running vibration detection inference."""

    def detect(self, model: ModelRecord, rows: list[dict]) -> DetectReport:
        """Run detection on Excel data rows.

        Note: The 'rows' parameter is legacy from mock implementation.
        We now expect the Excel DataFrame to be loaded separately.
        This method will be called from DetectService with proper data.
        """
        generated_at = datetime.now(timezone.utc).isoformat()
        window_detections = [
            WindowDetection(
                window_index=index,
                sample_start=0,
                sample_end=0,
                prediction="N/A",
                score=0.0,
                status="pending",
            )
            for index, _ in enumerate(rows, start=1)
        ]
        return DetectReport(
            excel_filename="data",
            model_name=model.display_name,
            prediction="N/A",
            confidence=0.0,
            status="pending",
            num_windows=len(rows),
            window_size=0,
            step_size=0,
            run_time_ms=0,
            generated_at=generated_at,
            class_probabilities=[],
            window_detections=window_detections,
        )

    def detect_from_excel(
        self,
        model: ModelRecord,
        excel_df,
        excel_filename: str = "data",
    ) -> DetectReport:
        """Run file-level detection on Excel DataFrame.

        Args:
            model: Model record with path to .pt file
            excel_df: pandas DataFrame with vibration data
            excel_filename: Name of Excel file for display purposes

        Returns:
            Rich detection report for the whole file and all windows

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

        started_at = perf_counter()
        model_path = Path(model.stored_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model.stored_path}")

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        checkpoint = torch.load(model_path, map_location=device, weights_only=False)

        classes = checkpoint.get("classes", [])
        cfg = checkpoint.get("cfg", {})
        cnn1d_params = checkpoint.get("cnn1d_params", {})
        meta = checkpoint.get("meta", {})

        if not classes:
            raise ValueError("Model checkpoint missing classes metadata")

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
            mean_probs = probs.mean(dim=0)
            confidence, prediction = torch.max(mean_probs, dim=0)

        pred_class_idx = int(prediction.item())
        pred_confidence = float(confidence.item())
        class_name = classes[pred_class_idx] if pred_class_idx < len(classes) else f"Class_{pred_class_idx}"
        status = "high_confidence" if pred_confidence > 0.8 else "review"

        mean_prob_values = mean_probs.detach().cpu().tolist()
        sorted_class_probs = sorted(
            ((label, float(prob)) for label, prob in zip(classes, mean_prob_values)),
            key=lambda item: item[1],
            reverse=True,
        )
        class_probabilities = [
            ClassProbability(rank=rank, class_name=label, probability=prob)
            for rank, (label, prob) in enumerate(sorted_class_probs, start=1)
        ]

        window_confidences, window_predictions = torch.max(probs, dim=1)
        window_confidence_values = window_confidences.detach().cpu().tolist()
        window_prediction_indices = window_predictions.detach().cpu().tolist()
        window_detections: list[WindowDetection] = []
        for index, (window_pred_idx, window_conf) in enumerate(
            zip(window_prediction_indices, window_confidence_values),
            start=1,
        ):
            window_class = classes[window_pred_idx] if window_pred_idx < len(classes) else f"Class_{window_pred_idx}"
            window_status = "high_confidence" if window_conf > 0.8 else "review"
            sample_start = (index - 1) * step
            sample_end = sample_start + window - 1
            window_detections.append(
                WindowDetection(
                    window_index=index,
                    sample_start=sample_start,
                    sample_end=sample_end,
                    prediction=window_class,
                    score=float(window_conf),
                    status=window_status,
                )
            )

        elapsed_ms = int((perf_counter() - started_at) * 1000)

        return DetectReport(
            excel_filename=excel_filename,
            model_name=model.display_name,
            prediction=class_name,
            confidence=pred_confidence,
            status=status,
            num_windows=num_windows,
            window_size=window,
            step_size=step,
            run_time_ms=elapsed_ms,
            generated_at=datetime.now(timezone.utc).isoformat(),
            class_probabilities=class_probabilities,
            window_detections=window_detections,
        )

