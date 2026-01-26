import argparse
from pathlib import Path

import pandas as pd

from .aggregation import AggregationConfig, aggregate_scored_flows
from .config import MODEL_FAMILY_AGG_THRESHOLDS, MODEL_FAMILY_THRESHOLDS
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


def _resolve_agg_theta_flow(
    parser: argparse.ArgumentParser, model_path: Path, theta_flow: float | None
) -> float:
    if theta_flow is not None:
        return theta_flow

    family = _infer_model_family(model_path)
    if family is None:
        parser.error(
            f"Unable to infer model family from '{model_path.name}'. "
            "Pass --agg-theta-flow explicitly."
        )

    try:
        return MODEL_FAMILY_AGG_THRESHOLDS[family]
    except KeyError:
        parser.error(
            f"No default aggregation threshold configured for model family '{family}'. "
            "Pass --agg-theta-flow explicitly."
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

    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="Enable windowed aggregation and alerting on scored flows",
    )
    parser.add_argument(
        "--agg-window-secs",
        type=int,
        default=60,
        help="Aggregation window size in seconds (default: 60)",
    )
    parser.add_argument(
        "--agg-allowed-lateness-secs",
        type=int,
        default=10,
        help="Allowed out-of-order lateness in seconds (default: 10)",
    )
    parser.add_argument(
        "--agg-theta-flow",
        type=float,
        default=None,
        help="Weak flow score threshold (defaults to model-family agg threshold)",
    )
    parser.add_argument(
        "--agg-theta-ratio",
        type=float,
        default=0.20,
        help="Alert ratio threshold within a window (default: 0.20)",
    )
    parser.add_argument(
        "--agg-min-flows",
        type=int,
        default=50,
        help="Minimum flows per window to evaluate alerts (default: 50)",
    )
    parser.add_argument(
        "--windows-out",
        default=None,
        help="Output CSV path for aggregated window metrics",
    )
    parser.add_argument(
        "--alerts-out",
        default=None,
        help="Output CSV path for aggregated alerts",
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

    if args.aggregate:
        theta_flow = _resolve_agg_theta_flow(parser, model_path, args.agg_theta_flow)
        cfg = AggregationConfig(
            window_secs=int(args.agg_window_secs),
            allowed_lateness_secs=int(args.agg_allowed_lateness_secs),
            group_bys=("src_ip", "src_ip,dst_port"),
            theta_flow=float(theta_flow),
            theta_ratio=float(args.agg_theta_ratio),
            min_flows=int(args.agg_min_flows),
        )

        windows_df, alerts_df = aggregate_scored_flows(result, cfg)

        if args.windows_out:
            windows_out = Path(args.windows_out)
        else:
            windows_out = output_path.with_name(f"{output_path.stem}-windows.csv")

        if args.alerts_out:
            alerts_out = Path(args.alerts_out)
        else:
            alerts_out = output_path.with_name(f"{output_path.stem}-alerts.csv")

        windows_out.parent.mkdir(parents=True, exist_ok=True)
        alerts_out.parent.mkdir(parents=True, exist_ok=True)

        windows_df.to_csv(windows_out, index=False)
        alerts_df.to_csv(alerts_out, index=False)

        print(f"[OK] Window metrics saved to {windows_out}")
        print(f"[OK] Alerts saved to {alerts_out}")
        if len(alerts_df) == 0:
            print("[i] No alerts triggered")
        else:
            print(
                alerts_df[
                    ["group_by", "group_key", "severity", "confidence", "reason"]
                ].head()
            )


if __name__ == "__main__":
    main()
