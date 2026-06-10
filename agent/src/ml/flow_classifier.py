"""Flow-based IDS inference for CICFlowMeter rows."""

from __future__ import annotations

from logging import Logger
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.config import settings
from src.ml.ids_schema import COLUMN_RENAME_MAP, FEATURE_COLUMNS


class FlowClassifier:
    """Scores CICFlowMeter-style flow rows with the trained IDS model."""

    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger
        self._model = None
        self._scaler = None
        self.available = False

        if not settings.anomaly_enabled:
            return

        model_path = Path(settings.flow_model_path)
        scaler_path = Path(settings.flow_scaler_path)
        if not model_path.exists():
            self._warn("Flow model unavailable at %s", model_path)
            return
        if not scaler_path.exists():
            self._warn("Flow scaler unavailable at %s", scaler_path)
            return

        try:
            self._model = joblib.load(model_path)
            self._scaler = joblib.load(scaler_path)
        except Exception as exc:  # noqa: BLE001 - model failure should not kill posture.
            self._warn("Failed to load flow model/scaler: %s", exc)
            return

        self.available = True
        self._info("Loaded flow IDS model=%s scaler=%s", model_path, scaler_path)

    def predict_with_metadata(self, flows: pd.DataFrame) -> pd.DataFrame:
        """Return input flow rows plus malicious score and prediction columns."""
        result = flows.rename(columns=COLUMN_RENAME_MAP).copy()
        if not self.available or self._model is None or self._scaler is None:
            result["malicious_score"] = 0.0
            result["prediction"] = 0
            result["prediction_label"] = "Unavailable"
            return result

        missing = set(FEATURE_COLUMNS) - set(result.columns)
        if missing:
            raise RuntimeError(f"Missing CICFlowMeter features: {sorted(missing)}")

        feature_df = _clean_flows_inference(result)
        scored = result.loc[feature_df.index].copy()
        if len(feature_df) == 0:
            scored["malicious_score"] = np.array([], dtype=float)
            scored["prediction"] = np.array([], dtype=int)
            scored["prediction_label"] = pd.Series([], dtype=object)
            return scored

        x_scaled = self._scaler.transform(feature_df[FEATURE_COLUMNS].values)
        if hasattr(self._model, "predict_proba"):
            scores = self._model.predict_proba(x_scaled)[:, 1]
        elif hasattr(self._model, "decision_function"):
            raw_scores = self._model.decision_function(x_scaled)
            scores = np.clip(0.5 - raw_scores, 0.0, 1.0)
        else:
            preds = self._model.predict(x_scaled)
            scores = np.array([1.0 if int(pred) in {-1, 1} else 0.0 for pred in preds])

        preds = (scores >= settings.flow_prediction_threshold).astype(int)
        scored["malicious_score"] = scores
        scored["prediction"] = preds
        scored["prediction_label"] = scored["prediction"].map({0: "Benign", 1: "Malicious"})
        return scored

    def _warn(self, message: str, *args: object) -> None:
        if self._logger:
            self._logger.warning(message, *args)

    def _info(self, message: str, *args: object) -> None:
        if self._logger:
            self._logger.info(message, *args)


def _clean_flows_inference(df: pd.DataFrame) -> pd.DataFrame:
    feature_df = df.loc[:, FEATURE_COLUMNS].copy()
    for col in FEATURE_COLUMNS:
        feature_df[col] = pd.to_numeric(feature_df[col], errors="coerce")

    feature_df = feature_df.replace([np.inf, -np.inf], np.nan)
    feature_df = feature_df.dropna()
    feature_df = feature_df[
        (feature_df["Flow Duration"] > 0)
        & ((feature_df["Tot Fwd Pkts"] + feature_df["Tot Bwd Pkts"]) > 0)
    ]
    return feature_df
