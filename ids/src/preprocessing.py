import numpy as np
import pandas as pd

from .config import FEATURE_COLUMNS, LABEL_COLUMN


def clean_flows(df: pd.DataFrame) -> pd.DataFrame:
    df = df[FEATURE_COLUMNS + [LABEL_COLUMN]]

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    df = df.drop_duplicates()

    df = df[(df["Flow Duration"] > 0) & ((df["Tot Fwd Pkts"] + df["Tot Bwd Pkts"]) > 0)]

    return df


def encode_binary_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[LABEL_COLUMN] = (df[LABEL_COLUMN] != "Benign").astype(int)
    return df
