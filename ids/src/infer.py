import argparse

import pandas as pd
from src.inference import TrafficClassifier


def main():
    parser = argparse.ArgumentParser(description="Network Traffic Inference")
    parser.add_argument("--model", required=True, help="Path to model.joblib")
    parser.add_argument("--scaler", required=True, help="Path to scaler.joblib")
    parser.add_argument("--input", required=True, help="CSV file for inference")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--output", default="predictions.csv")

    args = parser.parse_args()

    df = pd.read_csv(args.input)

    clf = TrafficClassifier(
        model_path=args.model,
        scaler_path=args.scaler,
        threshold=args.threshold,
    )

    result = clf.predict_with_metadata(df)
    result.to_csv(args.output, index=False)

    print(f"[✓] Predictions saved to {args.output}")
    print(result[["malicious_score", "prediction_label"]].head())


if __name__ == "__main__":
    main()
