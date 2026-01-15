import sys
from pathlib import Path

import numpy as np
import pandas as pd

INPUT_CSV = "02-14-2018.csv"  # path to ONE CIC-IDS2018 CSV file
OUTPUT_DIR = "cleaned"  # output directory

LABEL_COL = "Label"

ID_COLUMNS = ["Flow ID", "Src IP", "Dst IP", "Timestamp"]

LABEL_NORMALIZATION_MAP = {
    "DoSattacksHulk": "DoS_Hulk",
    "DoSattacksGoldenEye": "DoS_GoldenEye",
    "DoSattacksSlowloris": "DoS_Slowloris",
    "DoSattacksSlowHTTPTest": "DoS_SlowHTTPTest",
}

# ==============================
# SCRIPT
# ==============================


def main():
    input_path = Path(INPUT_CSV)
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"[+] Loading {input_path}")

    df = pd.read_csv(
        input_path,
        low_memory=False,
        na_values=["NaN", "Infinity", "-Infinity", "inf", "-inf", ""],
    )

    # ---- Step 1: normalize column names
    df.columns = df.columns.str.strip()

    # ---- Step 2: verify label column exists
    if LABEL_COL not in df.columns:
        print("[!] Label column not found")
        print("Available columns:", df.columns.tolist())
        sys.exit(1)

    # ---- Step 3: drop identifier / leakage columns
    drop_cols = [c for c in ID_COLUMNS if c in df.columns]
    df.drop(columns=drop_cols, inplace=True)

    # ---- Step 4: separate labels
    labels = df[LABEL_COL].astype(str)
    df.drop(columns=[LABEL_COL], inplace=True)

    # ---- Step 5: force numeric conversion
    df = df.apply(pd.to_numeric, errors="coerce")

    # ---- Step 6: remove invalid rows
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    valid_mask = df.notna().all(axis=1)

    df = df.loc[valid_mask].reset_index(drop=True)
    labels = labels.loc[valid_mask].reset_index(drop=True)

    # ---- Step 7: remove duplicate flows
    combined = pd.concat([df, labels], axis=1)
    combined = combined.drop_duplicates()
    df = combined.iloc[:, :-1]
    labels = combined.iloc[:, -1]

    # ---- Step 8: clean and normalize labels
    labels = labels.str.strip()
    labels = labels.str.replace(" ", "", regex=False)
    labels = labels.str.replace("-", "", regex=False)
    labels = labels.replace(LABEL_NORMALIZATION_MAP)

    print("[+] Labels after normalization:")
    print(labels.value_counts())

    # ---- Step 9: filter malicious-only
    malicious_mask = labels != "Benign"
    X = df.loc[malicious_mask].reset_index(drop=True)
    y = labels.loc[malicious_mask].reset_index(drop=True)

    # ---- Step 10: drop zero-variance features
    variance = X.var()
    X = X.loc[:, variance > 0]

    # ---- Step 11: final sanity checks
    assert X.isna().sum().sum() == 0, "NaN detected after cleaning"
    assert np.isfinite(X.values).all(), "Inf detected after cleaning"
    assert len(X) == len(y), "Feature/label size mismatch"

    print(f"[+] Final malicious samples: {len(X)}")
    print(f"[+] Final feature count: {X.shape[1]}")

    # ---- Step 12: save outputs
    X_path = output_path / "X_clean.csv"
    y_path = output_path / "y_clean.csv"
    feat_path = output_path / "features.txt"

    X.to_csv(X_path, index=False)
    y.to_csv(y_path, index=False)

    with open(feat_path, "w") as f:
        for col in X.columns:
            f.write(col + "\n")

    print("[+] Cleaning completed successfully")
    print(f"[+] Saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
