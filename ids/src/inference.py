from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .config import FEATURE_COLUMNS


class TrafficClassifier:
    """
    Deployment-safe inference wrapper.
    """

    def __init__(
        self,
        model_path: str,
        scaler_path: str,
        threshold: float = 0.5,
    ):
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.threshold = threshold

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        if not self.scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found: {self.scaler_path}")

        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)

    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Ensures correct feature order, type, and scaling.
        """
        missing = set(FEATURE_COLUMNS) - set(df.columns)
        if missing:
            raise RuntimeError(f"Missing required features: {missing}")

        X = df[FEATURE_COLUMNS].copy()

        # Enforce numeric
        for col in FEATURE_COLUMNS:
            X[col] = pd.to_numeric(X[col], errors="coerce")

        if X.isna().any().any():
            raise RuntimeError("NaNs detected after numeric coercion")

        return self.scaler.transform(X.values)

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """
        Returns malicious probability.
        """
        X = self._prepare_features(df)
        return self.model.predict_proba(X)[:, 1]

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Returns binary prediction using configured threshold.
        """
        scores = self.predict_proba(df)
        return (scores >= self.threshold).astype(int)

    def predict_with_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns predictions + probabilities.
        """
        scores = self.predict_proba(df)
        preds = (scores >= self.threshold).astype(int)

        result = df.copy()
        result["malicious_score"] = scores
        result["prediction"] = preds
        result["prediction_label"] = result["prediction"].map(
            {0: "Benign", 1: "Malicious"}
        )

        return result
