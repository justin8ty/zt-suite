from pathlib import Path

import joblib
from xgboost import XGBClassifier


def build_model(random_state: int = 42) -> XGBClassifier:
    return XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        scale_pos_weight=1,  # override dynamically if needed
        n_jobs=-1,
        random_state=random_state,
        tree_method="hist",
    )


def train_model(model, X_train, y_train):
    model.fit(X_train, y_train)
    return model


def save_model(model, output_path: str):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
