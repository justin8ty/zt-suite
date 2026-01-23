from pathlib import Path

import joblib
import pandas as pd

from src.config import FEATURE_COLUMNS, LABEL_COLUMN
from src.data_loader import load_csv_directory
from src.evaluate import evaluate_binary
from src.feature_importance import get_feature_importance, sanity_check_importance
from src.model import build_model, save_model, train_model
from src.preprocessing import clean_flows, encode_binary_labels, scale_features
from src.split import train_test_split_session

RAW_DATA_DIR = "data/raw"
MODEL_OUTPUT_PATH = "models/binary_rf.joblib"


def main():
    print("[*] Loading data...")
    df = load_csv_directory(RAW_DATA_DIR)

    print("[*] Cleaning data...")
    df = clean_flows(df)

    print("[*] Encoding labels...")
    df = encode_binary_labels(df)

    print("[*] Splitting dataset...")
    X_train_raw, X_test_raw, y_train, y_test = train_test_split_session(df)

    print("[*] Scaling features...")
    X_train, scaler = scale_features(pd.DataFrame(X_train_raw, columns=FEATURE_COLUMNS))
    X_test, _ = scale_features(
        pd.DataFrame(X_test_raw, columns=FEATURE_COLUMNS), scaler=scaler
    )

    # Save scaler for deployment
    joblib.dump(scaler, "scaler.joblib")

    print("[*] Building model...")
    model = build_model()

    print("[*] Training model...")
    model = train_model(model, X_train, y_train)

    print("[*] Evaluating model...")
    metrics = evaluate_binary(model, X_test, y_test)

    print(metrics["classification_report"])
    print("Confusion Matrix:")
    print(metrics["confusion_matrix"])
    print(f"Recall (Malicious): {metrics['recall']:.4f}")

    print("[*] Inspecting feature importance...")
    fi = get_feature_importance(model)
    print(fi)

    sanity_check_importance(fi)

    print("[*] Saving model...")
    save_model(model, MODEL_OUTPUT_PATH)

    print("[✓] Training complete.")


if __name__ == "__main__":
    main()
