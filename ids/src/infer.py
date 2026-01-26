import argparse
from pathlib import Path

import pandas as pd

from .config import MODEL_FAMILY_THRESHOLDS
from .inference import TrafficClassifier


def _default_scaler_path(model_path: Path) -> Path:
    """Infer scaler path from model filename.

    Examples:
    - models/xgb.joblib     -> models/scaler.joblib
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


def _infer_model_family(model_path: Path) -> str | None:
    stem = model_path.stem
    if stem.startswith("xgb"):
        return "xgb"
    if stem.startswith("rf"):
        return "rf"
    return None


def _resolve_threshold(
    parser: argparse.ArgumentParser, model_path: Path, threshold: float | None
) -> float:
    if threshold is not None:
        return threshold

    family = _infer_model_family(model_path)
    if family is None:
        parser.error(
            f"Unable to infer model family from '{model_path.name}'. "
            "Pass --threshold explicitly."
        )

    try:
        return MODEL_FAMILY_THRESHOLDS[family]
    except KeyError:
        parser.error(
            f"No default threshold configured for model family '{family}'. "
            "Pass --threshold explicitly."
        )
        raise


def main():
    parser = argparse.ArgumentParser(description="Network Traffic Inference")
    parser.add_argument("--model", required=True, help="Path to model.joblib")
    parser.add_argument(
        "--scaler",
        default=None,
        help="Path to scaler.joblib (defaults to matching scaler next to model)",
    )
    parser.add_argument("--input", required=True, help="CSV file for inference")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Override decision threshold (defaults to model-family threshold)",
    )
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

    threshold = _resolve_threshold(parser, model_path, args.threshold)
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
        threshold=threshold,
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
