from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .config import COLUMN_RENAME_MAP, FEATURE_COLUMNS
from .preprocessing import clean_flows_inference


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

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize inference CSV column names to training schema.
        """
        return df.rename(columns=COLUMN_RENAME_MAP)

    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Enforces feature schema, cleaning, and scaling.
        """
        df = self._normalize_columns(df)

        missing = set(FEATURE_COLUMNS) - set(df.columns)
        if missing:
            raise RuntimeError(f"Missing required features: {missing}")

        df = clean_flows_inference(df)

        X = df[FEATURE_COLUMNS].values
        return self.scaler.transform(X)

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        X = self._prepare_features(df)
        return self.model.predict_proba(X)[:, 1]

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        scores = self.predict_proba(df)
        return (scores >= self.threshold).astype(int)

    def predict_with_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        df_norm = self._normalize_columns(df)

        scores = self.predict_proba(df_norm)
        preds = (scores >= self.threshold).astype(int)

        result = df_norm.loc[: len(preds) - 1].copy()
        result["malicious_score"] = scores
        result["prediction"] = preds
        result["prediction_label"] = result["prediction"].map(
            {0: "Benign", 1: "Malicious"}
        )

        return result
