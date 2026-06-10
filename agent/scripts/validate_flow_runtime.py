"""Throwaway runtime validation for PCAP -> CICFlowMeter -> model inference.

Run from agent/:
    uv run python scripts/validate_flow_runtime.py --pcap path/to/sample.pcap
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ml.flow_classifier import FlowClassifier  # noqa: E402
from src.ml.ids_schema import COLUMN_RENAME_MAP, FEATURE_COLUMNS  # noqa: E402
from src.services.cicflowmeter import pcap_to_flows  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate runtime PCAP -> CICFlowMeter -> IDS model scoring."
    )
    parser.add_argument("--pcap", required=True, help="Input PCAP file")
    parser.add_argument(
        "--csv-out",
        default=None,
        help="Optional CICFlowMeter CSV output path; defaults to <pcap>.flows.csv",
    )
    args = parser.parse_args()

    pcap_path = Path(args.pcap)
    csv_path = Path(args.csv_out) if args.csv_out else pcap_path.with_suffix(".flows.csv")

    if not pcap_path.exists():
        print(f"[FAIL] PCAP not found: {pcap_path}")
        return 1

    flows = pcap_to_flows(pcap_path, csv_path)
    print(f"[OK] CICFlowMeter rows: {len(flows)}")
    print(f"[OK] CICFlowMeter CSV: {csv_path}")

    if len(flows) == 0:
        print("[FAIL] No flows emitted from PCAP")
        return 1

    normalized = flows.rename(columns=COLUMN_RENAME_MAP)
    missing = sorted(set(FEATURE_COLUMNS) - set(normalized.columns))
    if missing:
        print(f"[FAIL] Missing model feature columns: {missing}")
        return 1
    print(f"[OK] Required model columns present: {len(FEATURE_COLUMNS)}")

    classifier = FlowClassifier()
    if not classifier.available:
        print("[FAIL] FlowClassifier unavailable; check model/scaler env paths")
        return 1

    scored = classifier.predict_with_metadata(flows)
    if len(scored) == 0:
        print("[FAIL] Model preprocessing dropped all flows")
        return 1

    scores = pd.to_numeric(scored["malicious_score"], errors="coerce").fillna(0)
    predictions = pd.to_numeric(scored["prediction"], errors="coerce").fillna(0)
    print(f"[OK] Scored rows: {len(scored)}")
    print(f"[OK] Max malicious_score: {scores.max():.4f}")
    print(f"[OK] Malicious predictions: {int(predictions.sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
