import os
import json
import joblib
import numpy as np
import pandas as pd

import mlflow


PROCESSED_PATH = "data/processed/ev_energy_processed.csv"
MODEL_PATH = "model/ev_energy_model.pkl"

ANOMALY_CONFIG_PATH = "model/anomaly_config.json"
BASELINE_STATS_PATH = "model/baseline_stats.json"

# MLflow local tracking (même experiment)
MLFLOW_TRACKING_URI = "./mlruns"
MLFLOW_EXPERIMENT_NAME = "ev-energy-consumption"


NUM_FEATURES = [
    "Speed_kmh",
    "Acceleration_ms2",
    "Slope_%",
    "Temperature_C",
    "Battery_State_%"
]
CAT_FEATURES = [
    "Driving_Mode",
    "Traffic_Condition"
]
TARGET = "Energy_Consumption_kWh"


def safe_div(a: np.ndarray, b: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    return a / (np.abs(b) + eps)


def main() -> None:
    if not os.path.exists(PROCESSED_PATH):
        raise FileNotFoundError(f"Processed dataset not found: {PROCESSED_PATH}")
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    df = pd.read_csv(PROCESSED_PATH)

    X = df[NUM_FEATURES + CAT_FEATURES].copy()
    y = df[TARGET].to_numpy()

    pipeline = joblib.load(MODEL_PATH)
    y_pred = pipeline.predict(X)

    residual = y - y_pred
    error_pct = safe_div(residual, y_pred) * 100.0  # % difference vs predicted

    # --- Anomaly thresholds (simple + robuste)
    # For "high consumption anomaly", we care mainly about residual > 0 (actual > predicted)
    pos_residual = residual[residual > 0]
    pos_error_pct = error_pct[error_pct > 0]

    # Use high quantiles as thresholds
    residual_thr = float(np.quantile(pos_residual, 0.95)) if len(pos_residual) else float(np.quantile(residual, 0.95))
    error_pct_thr = float(np.quantile(pos_error_pct, 0.95)) if len(pos_error_pct) else float(np.quantile(error_pct, 0.95))

    anomaly_config = {
        "method": "regression_residual",
        "residual_threshold_kwh_p95": residual_thr,
        "error_pct_threshold_p95": error_pct_thr,
        "rule": "anomaly if residual > residual_threshold OR error_pct > error_pct_threshold",
        # for streaming alerting (we'll use these later in API)
        "alert_window_size": 20,
        "alert_min_anomalies_in_window": 10,
        "alert_consecutive_anomalies": 5
    }

    os.makedirs("model", exist_ok=True)
    with open(ANOMALY_CONFIG_PATH, "w") as f:
        json.dump(anomaly_config, f, indent=2)

    # --- Baseline stats for drift detection (training reference)
    # We'll store stats for selected numeric features + target
    baseline_cols = NUM_FEATURES + [TARGET]
    baseline_stats = {}

    for c in baseline_cols:
        arr = pd.to_numeric(df[c], errors="coerce").dropna().to_numpy()
        baseline_stats[c] = {
            "count": int(len(arr)),
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "p25": float(np.quantile(arr, 0.25)),
            "p50": float(np.quantile(arr, 0.50)),
            "p75": float(np.quantile(arr, 0.75)),
            "p95": float(np.quantile(arr, 0.95)),
            "max": float(np.max(arr)),
        }

    with open(BASELINE_STATS_PATH, "w") as f:
        json.dump(baseline_stats, f, indent=2)

    # --- Log to MLflow (nice for MLOps)
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    with mlflow.start_run(run_name="thresholds-and-baseline-v1"):
        mlflow.log_artifact(ANOMALY_CONFIG_PATH)
        mlflow.log_artifact(BASELINE_STATS_PATH)
        mlflow.log_metrics({
            "residual_threshold_kwh_p95": residual_thr,
            "error_pct_threshold_p95": error_pct_thr
        })
        mlflow.set_tags({
            "task": "anomaly_thresholding_and_drift_baseline",
            "project": "ev-energy-mlops-pipeline"
        })

    print("✅ Eval done!")
    print(f"Saved anomaly config -> {ANOMALY_CONFIG_PATH}")
    print(f"Saved baseline stats -> {BASELINE_STATS_PATH}")
    print("\nThresholds:")
    print(f"  residual_threshold_kwh_p95 = {residual_thr:.4f}")
    print(f"  error_pct_threshold_p95     = {error_pct_thr:.2f}%")
    print("\nAlerting rules (streaming):")
    print("  window_size=20, min_anomalies=10, consecutive=5")


if __name__ == "__main__":
    main()
