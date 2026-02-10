from __future__ import annotations

from app.domain.entities import DetectRowResult, ModelRecord


class DetectorGateway:
    def detect(self, model: ModelRecord, rows: list[dict]) -> list[DetectRowResult]:
        results: list[DetectRowResult] = []
        for index, row in enumerate(rows, start=1):
            input_preview = str(row.get("input", ""))
            seed = sum(ord(ch) for ch in f"{model.id}:{input_preview}")
            is_anomaly = seed % 2 == 1
            prediction = "Anomaly" if is_anomaly else "Normal"
            score = min(0.99, 0.50 + ((seed % 49) / 100.0))
            status = "review" if is_anomaly else "ok"
            results.append(
                DetectRowResult(
                    row_index=index,
                    input_preview=input_preview,
                    prediction=prediction,
                    score=score,
                    status=status,
                )
            )
        return results
