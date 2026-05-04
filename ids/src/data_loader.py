from pathlib import Path

import pandas as pd


def load_csv_directory(csv_dir: str) -> pd.DataFrame:
    csv_dir = Path(csv_dir)
    csv_files = sorted(csv_dir.glob("*.csv"))

    if not csv_files:
        raise RuntimeError(f"No CSV files found in {csv_dir}")

    dataframes = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        dataframes.append(df)

    return pd.concat(dataframes, ignore_index=True)
