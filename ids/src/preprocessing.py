import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from .config import FEATURE_COLUMNS, LABEL_COLUMN


def clean_flows(df: pd.DataFrame) -> pd.DataFrame:
    df = df[FEATURE_COLUMNS + [LABEL_COLUMN]]

    # Convert all feature columns to numeric, coerce errors to NaN
    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Replace infinities, drop NaNs and duplicates
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    df = df.drop_duplicates()

    # Remove flows with zero duration or zero packets
    df = df[(df["Flow Duration"] > 0) & ((df["Tot Fwd Pkts"] + df["Tot Bwd Pkts"]) > 0)]

    return df


def encode_binary_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[LABEL_COLUMN] = (df[LABEL_COLUMN] != "Benign").astype(int)
    return df


def scale_features(df: pd.DataFrame, scaler: StandardScaler = None):
    """
    Scale features using StandardScaler.
    If scaler is provided, use it; otherwise, fit a new one.
    Returns scaled features and the scaler used.
    """
    X = df[FEATURE_COLUMNS].values

    if scaler is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = scaler.transform(X)

    return X_scaled, scaler
