import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

MODEL_DIR = "model"

# ------------------
# Load artifacts
# ------------------

model = joblib.load(Path(MODEL_DIR) / "rf_model.pkl")
scaler = joblib.load(Path(MODEL_DIR) / "scaler.pkl")

with open(Path(MODEL_DIR) / "label_map.json") as f:
    label_map = json.load(f)

inv_label_map = {v: k for k, v in label_map.items()}

with open("cleaned/features.txt") as f:
    feature_order = [line.strip() for line in f]

# ------------------
# Example: load new flows
# ------------------
# This CSV must contain EXACTLY the same features

new_flows = pd.read_csv("new_flows.csv")

# Enforce schema
new_flows = new_flows[feature_order]

# Scale
X_scaled = scaler.transform(new_flows)

# Predict
pred_classes = model.predict(X_scaled)
pred_probs = model.predict_proba(X_scaled)

# Output
for i in range(len(new_flows)):
    cls = pred_classes[i]
    attack = inv_label_map[cls]
    confidence = np.max(pred_probs[i])

    print(f"Flow {i}: {attack} ({confidence:.4f})")
