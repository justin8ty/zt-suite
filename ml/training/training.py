import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

# ======================
# CONFIG
# ======================

DATA_DIR = "cleaned"
X_FILE = "X_clean.csv"
Y_FILE = "y_clean.csv"

OUTPUT_DIR = "model"
N_ESTIMATORS = 300
RANDOM_STATE = 42

# ======================
# LOAD DATA
# ======================

X = pd.read_csv(Path(DATA_DIR) / X_FILE)
y = pd.read_csv(Path(DATA_DIR) / Y_FILE).iloc[:, 0]

print("[+] Loaded data")
print("Samples:", len(X))
print("Features:", X.shape[1])
print("Classes:", y.nunique())

# ======================
# LABEL ENCODING
# ======================

label_names = sorted(y.unique())
label_map = {name: idx for idx, name in enumerate(label_names)}
y_encoded = y.map(label_map)

print("[+] Label mapping:")
print(label_map)

# ======================
# TRAIN / TEST SPLIT
# ======================

from sklearn.model_selection import StratifiedShuffleSplit

splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)

for train_idx, test_idx in splitter.split(X, y_encoded):
    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y_encoded.iloc[train_idx]
    y_test = y_encoded.iloc[test_idx]


# ======================
# FEATURE SCALING
# ======================

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ======================
# MODEL TRAINING
# ======================

model = RandomForestClassifier(
    n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1, class_weight=None
)

print("[+] Training model...")
model.fit(X_train_scaled, y_train)

# ======================
# EVALUATION
# ======================

y_pred = model.predict(X_test_scaled)

print("\n=== CLASSIFICATION REPORT ===")
print(classification_report(y_test, y_pred, target_names=label_names))

print("=== CONFUSION MATRIX ===")
print(confusion_matrix(y_test, y_pred))

# ======================
# SAVE ARTIFACTS
# ======================

output = Path(OUTPUT_DIR)
output.mkdir(parents=True, exist_ok=True)

joblib.dump(model, output / "rf_model.pkl")
joblib.dump(scaler, output / "scaler.pkl")

with open(output / "label_map.json", "w") as f:
    json.dump(label_map, f, indent=2)

print("[+] Model saved to ./model/")
