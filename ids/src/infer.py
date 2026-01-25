import argparse
from pathlib import Path

import pandas as pd

from .inference import TrafficClassifier


def _default_scaler_path(model_path: Path) -> Path:
    """Infer scaler path from model filename.

    Examples:
    - models/xgb-pre.joblib -> models/scaler-pre.joblib
    - models/rf-exp.joblib  -> models/scaler-exp.joblib
    - models/xgb1.joblib    -> models/scaler1.joblib
    Fallback:
    - models/scaler.joblib
    """

    model_stem = model_path.stem
    variant = ""

    if model_stem.startswith("xgb"):
        variant = model_stem[len("xgb") :]
    elif model_stem.startswith("rf"):
        variant = model_stem[len("rf") :]

    candidate = (
        model_path.with_name(f"scaler{variant}.joblib")
        if variant
        else model_path.with_name("scaler.joblib")
    )
    if candidate.exists():
        return candidate

    fallback = model_path.with_name("scaler.joblib")
    return fallback


def main():
    parser = argparse.ArgumentParser(description="Network Traffic Inference")
    parser.add_argument("--model", required=True, help="Path to model.joblib")
    parser.add_argument(
        "--scaler",
        default=None,
        help="Path to scaler.joblib (defaults to matching scaler next to model)",
    )
    parser.add_argument("--input", required=True, help="CSV file for inference")
    parser.add_argument("--threshold", type=float, default=0.4)
    parser.add_argument(
        "--output-dir",
        default="data/flows-results",
        help="Directory to save inference results",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path (defaults to <output-dir>/<input>-<model>.csv)",
    )

    args = parser.parse_args()

    model_path = Path(args.model)
    input_path = Path(args.input)

    scaler_path = Path(args.scaler) if args.scaler else _default_scaler_path(model_path)

    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path(args.output_dir)
        output_path = output_dir / f"{input_path.stem}-{model_path.stem}.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    input_rows = len(df)

    clf = TrafficClassifier(
        model_path=str(model_path),
        scaler_path=str(scaler_path),
        threshold=args.threshold,
    )

    result = clf.predict_with_metadata(df)
    result.to_csv(output_path, index=False)

    dropped = input_rows - len(result)

    print(f"[OK] Predictions saved to {output_path}")
    if dropped > 0:
        print(f"[i] Dropped {dropped} rows during cleaning")
    print(result[["malicious_score", "prediction_label"]].head())


if __name__ == "__main__":
    main()
