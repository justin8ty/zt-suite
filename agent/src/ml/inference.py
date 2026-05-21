"""Local anomaly detection for engineered traffic features."""

from __future__ import annotations

from datetime import datetime, timezone
from logging import Logger
from pathlib import Path
from uuid import uuid4

from src.config import settings
from src.models.alert import AlertRecord, AnomalyResult
from src.models.features import TrafficFeatureVector

try:
    import joblib
except ImportError:  # pragma: no cover - optional until real model is packaged.
    joblib = None


class AnomalyDetector:
    """Scores traffic feature vectors with a local model or heuristic fallback."""

    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger
        self._model = None
        self._model_available = False

        if not settings.anomaly_enabled:
            return

        model_path = Path(settings.anomaly_model_path)
        if model_path.exists() and joblib is not None:
            try:
                self._model = joblib.load(model_path)
                self._model_available = True
                if self._logger:
                    self._logger.info("Loaded anomaly model from %s", model_path)
            except Exception as exc:  # noqa: BLE001 - model failure should not kill agent.
                if self._logger:
                    self._logger.warning("Failed to load anomaly model: %s", exc)
        elif self._logger:
            self._logger.warning(
                "Anomaly model unavailable at %s; using heuristic fallback",
                model_path,
            )

    def score(self, features: TrafficFeatureVector) -> AnomalyResult:
        """Score one feature vector."""
        if not settings.anomaly_enabled:
            return AnomalyResult(
                batch_id=features.batch_id,
                anomalous=False,
                score=0.0,
                threshold=settings.anomaly_threshold,
                detection_source="disabled",
            )

        if self._model_available and self._model is not None:
            model_score = self._score_with_model(features)
            return AnomalyResult(
                batch_id=features.batch_id,
                anomalous=model_score >= settings.anomaly_threshold,
                score=model_score,
                threshold=settings.anomaly_threshold,
                detection_source="model",
                reason_codes=["model_score_threshold"]
                if model_score >= settings.anomaly_threshold
                else [],
            )

        return self._score_with_heuristics(features)

    def build_alert(
        self,
        features: TrafficFeatureVector,
        result: AnomalyResult,
    ) -> AlertRecord | None:
        """Create an alert record for anomalous results."""
        if not result.anomalous:
            return None

        severity = _severity_from_score(result.score)
        return AlertRecord(
            alert_id=str(uuid4()),
            agent_id=features.agent_id,
            batch_id=features.batch_id,
            created_at=datetime.now(timezone.utc),
            severity=severity,
            confidence=result.score,
            anomaly_score=result.score,
            reason_codes=result.reason_codes,
            message="Anomalous traffic batch detected by endpoint agent",
        )

    def _score_with_model(self, features: TrafficFeatureVector) -> float:
        values = [[
            features.packet_count,
            features.byte_count,
            features.packets_per_minute,
            features.bytes_per_minute,
            features.unique_dst_ip_count,
            features.unique_dst_port_count,
            features.average_packet_size,
            features.tcp_packet_count,
            features.udp_packet_count,
            features.syn_ratio,
            features.ack_ratio,
            features.fin_ratio,
            features.rst_ratio,
            features.psh_ratio,
            features.urg_ratio,
            features.well_known_port_ratio,
            features.ephemeral_port_ratio,
        ]]

        if hasattr(self._model, "predict_proba"):
            return float(self._model.predict_proba(values)[0][1])

        if hasattr(self._model, "decision_function"):
            raw_score = float(self._model.decision_function(values)[0])
            # Normalize rough IsolationForest-style decision score to 0..1, where
            # lower decision values are more anomalous.
            return max(0.0, min(1.0, 0.5 - raw_score))

        if hasattr(self._model, "predict"):
            pred = int(self._model.predict(values)[0])
            return 1.0 if pred in {-1, 1} else 0.0

        return 0.0

    def _score_with_heuristics(self, features: TrafficFeatureVector) -> AnomalyResult:
        reason_codes: list[str] = []
        score = 0.0

        if features.unique_dst_port_count >= settings.heuristic_unique_dst_port_threshold:
            reason_codes.append("high_unique_dst_ports")
            score += 0.35

        if features.syn_ratio >= settings.heuristic_syn_ratio_threshold and features.tcp_packet_count >= 20:
            reason_codes.append("high_syn_ratio")
            score += 0.30

        if features.packets_per_minute >= settings.heuristic_packets_per_minute_threshold:
            reason_codes.append("high_packets_per_minute")
            score += 0.35

        score = min(score, 1.0)
        return AnomalyResult(
            batch_id=features.batch_id,
            anomalous=score >= settings.anomaly_threshold,
            score=score,
            threshold=settings.anomaly_threshold,
            detection_source="heuristic",
            reason_codes=reason_codes,
        )


def _severity_from_score(score: float) -> str:
    if score >= 0.9:
        return "critical"
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"
