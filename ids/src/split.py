import pandas as pd
from sklearn.model_selection import train_test_split

from .config import FEATURE_COLUMNS, LABEL_COLUMN


def train_test_split_session(
    df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
):
    """
    Split dataset by pseudo-session to avoid leakage.
    Creates session_id from Dst Port, Flow Duration, Tot Fwd Pkts, Tot Bwd Pkts
    """
    df = df.copy()
    # Generate pseudo-session
    df["session_id"] = (
        df["Dst Port"].astype(str)
        + "_"
        + df["Flow Duration"].astype(str)
        + "_"
        + df["Tot Fwd Pkts"].astype(str)
        + "_"
        + df["Tot Bwd Pkts"].astype(str)
    )

    # Map each session to its dominant label
    session_labels = (
        df.groupby("session_id")[LABEL_COLUMN].agg(lambda x: x.mode()[0]).reset_index()
    )

    # Split sessions
    train_sessions, test_sessions = train_test_split(
        session_labels["session_id"],
        test_size=test_size,
        stratify=session_labels[LABEL_COLUMN],
        random_state=random_state,
    )

    # Select rows for train/test
    train_df = df[df["session_id"].isin(train_sessions)]
    test_df = df[df["session_id"].isin(test_sessions)]

    # Extract features and labels
    X_train = train_df[FEATURE_COLUMNS].to_numpy()
    y_train = train_df[LABEL_COLUMN].to_numpy()
    X_test = test_df[FEATURE_COLUMNS].to_numpy()
    y_test = test_df[LABEL_COLUMN].to_numpy()

    return X_train, X_test, y_train, y_test
