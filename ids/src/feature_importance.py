import numpy as np
import pandas as pd

from .config import FEATURE_COLUMNS


def get_feature_importance(model, top_n: int = 20) -> pd.DataFrame:
    if not hasattr(model, "feature_importances_"):
        raise RuntimeError("Model does not expose feature_importances_")

    importances = model.feature_importances_
    total = importances.sum()

    df = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance": importances,
            "importance_pct": (importances / total) * 100,
        }
    )

    return df.sort_values("importance", ascending=False).head(top_n)


def sanity_check_importance(df: pd.DataFrame):
    top_feature = df.iloc[0]
    if top_feature["importance_pct"] > 40:
        raise RuntimeError(
            f"Feature dominance detected: {top_feature['feature']} "
            f"accounts for {top_feature['importance_pct']:.2f}% of importance"
        )
