from sklearn.model_selection import train_test_split

from .config import FEATURE_COLUMNS, LABEL_COLUMN


def train_test_split_stratified(df, test_size: float = 0.2, random_state: int = 42):
    X = df[FEATURE_COLUMNS].values
    y = df[LABEL_COLUMN].values

    return train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )
