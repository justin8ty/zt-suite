import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from config import FEATURE_COLUMNS, LABEL_COLUMN


def clean_flows(df: pd.DataFrame) -> pd.DataFrame:
    df = df[FEATURE_COLUMNS + [LABEL_COLUMN]]

    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    df = df.drop_duplicates()

    df = df[(df["Flow Duration"] > 0) & ((df["Tot Fwd Pkts"] + df["Tot Bwd Pkts"]) > 0)]

    return df


def clean_flows_inference(df: pd.DataFrame) -> pd.DataFrame:
    """
    Label-free cleaning for inference.
    Mirrors training preprocessing.
    """
    df = df[FEATURE_COLUMNS].copy()

    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()

    df = df[(df["Flow Duration"] > 0) & ((df["Tot Fwd Pkts"] + df["Tot Bwd Pkts"]) > 0)]

    return df


def encode_binary_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[LABEL_COLUMN] = (df[LABEL_COLUMN] != "Benign").astype(int)
    return df


def scale_features(df: pd.DataFrame, scaler: StandardScaler = None):
    X = df[FEATURE_COLUMNS].values

    if scaler is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = scaler.transform(X)

    return X_scaled, scaler
