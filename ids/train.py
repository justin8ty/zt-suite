from pathlib import Path

import joblib
import pandas as pd
from sklearn.utils.class_weight import compute_sample_weight

from src.config import FEATURE_COLUMNS
from src.data_loader import load_csv_directory
from src.evaluate import evaluate_binary
from src.feature_importance import get_feature_importance, sanity_check_importance
from src.model import (
    build_model as build_xgb_model,
)
from src.model import (
    build_mlp_model,
    build_rf_model,
    save_model,
)
from src.preprocessing import (
    clean_flows,
    encode_binary_labels,
    scale_features,
)
from src.split import train_test_split_session

RAW_DATA_DIR = "data/raw"
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)


def compute_scale_pos_weight(y):
    benign = (y == 0).sum()
    malicious = (y == 1).sum()
    return benign / malicious


def compute_sample_weights(y):
    return compute_sample_weight(class_weight="balanced", y=y)


def train_and_evaluate(
    name: str,
    model,
    X_train,
    y_train,
    X_test,
    y_test,
    sample_weight=None,
):
    print(f"\n[*] Training {name}...")
    if sample_weight is not None:
        model.fit(X_train, y_train, sample_weight=sample_weight)
    else:
        model.fit(X_train, y_train)

    print(f"[*] Evaluating {name}...")
    metrics = evaluate_binary(model, X_test, y_test)

    print(metrics["classification_report"])
    print("Confusion Matrix:")
    print(metrics["confusion_matrix"])
    print(f"Recall (Malicious): {metrics['recall']:.4f}")

    if hasattr(model, "feature_importances_"):
        print(f"[*] Inspecting feature importance for {name}...")
        fi = get_feature_importance(model)
        print(fi)
        sanity_check_importance(fi)

    output_path = MODEL_DIR / f"{name}.joblib"
    save_model(model, output_path)
    print(f"[OK] Saved {name} -> {output_path}")


def main():
    print("[*] Loading data...")
    df = load_csv_directory(RAW_DATA_DIR)

    print("[*] Cleaning data...")
    df = clean_flows(df)

    print("[*] Encoding labels...")
    df = encode_binary_labels(df)

    print("[*] Performing session-based split...")
    X_train_raw, X_test_raw, y_train, y_test = train_test_split_session(df)

    print("[*] Scaling features (fit on TRAIN only)...")
    X_train_df = pd.DataFrame(X_train_raw, columns=FEATURE_COLUMNS)
    X_test_df = pd.DataFrame(X_test_raw, columns=FEATURE_COLUMNS)

    X_train, scaler = scale_features(X_train_df)
    X_test, _ = scale_features(X_test_df, scaler=scaler)

    joblib.dump(scaler, MODEL_DIR / "scaler.joblib")
    print("[OK] Scaler saved")

    print("[*] Preparing models...")
    scale_pos_weight = compute_scale_pos_weight(y_train)
    sample_weights = compute_sample_weights(y_train)

    models = {
        "rf": (build_rf_model(), None),
        "xgb": (
            build_xgb_model(random_state=42).set_params(
                scale_pos_weight=scale_pos_weight
            ),
            None,
        ),
        "mlp": (build_mlp_model(), sample_weights),
    }

    for name, (model, sample_weight) in models.items():
        train_and_evaluate(
            name=name,
            model=model,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            sample_weight=sample_weight,
        )

    print("\n[OK] All models trained successfully.")


if __name__ == "__main__":
    main()
