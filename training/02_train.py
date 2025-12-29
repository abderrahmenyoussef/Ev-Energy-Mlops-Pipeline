import os
import json
import joblib
import pandas as pd
import numpy as np

import mlflow
import mlflow.sklearn

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import matplotlib.pyplot as plt


PROCESSED_PATH = "data/processed/ev_energy_processed.csv"
MODEL_DIR = "model"
ARTIFACT_DIR = "artifacts"
MODEL_PATH = os.path.join(MODEL_DIR, "ev_energy_model.pkl")
FEATURE_CONFIG_PATH = os.path.join(MODEL_DIR, "feature_config.json")

# MLflow local tracking
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


def plot_pred_vs_actual(y_true: np.ndarray, y_pred: np.ndarray, out_path: str) -> None:
    plt.figure(figsize=(8, 6))
    plt.scatter(y_true, y_pred)
    plt.xlabel("Actual Energy (kWh)")
    plt.ylabel("Predicted Energy (kWh)")
    plt.title("Predicted vs Actual")

    mn = min(y_true.min(), y_pred.min())
    mx = max(y_true.max(), y_pred.max())
    plt.plot([mn, mx], [mn, mx])

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def plot_residuals(y_true: np.ndarray, y_pred: np.ndarray, out_path: str) -> None:
    residuals = y_true - y_pred
    plt.figure(figsize=(8, 6))
    plt.hist(residuals, bins=40)
    plt.xlabel("Residual (Actual - Predicted)")
    plt.ylabel("Count")
    plt.title("Residuals Distribution")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()


def main() -> None:
    if not os.path.exists(PROCESSED_PATH):
        raise FileNotFoundError(f"Processed dataset not found: {PROCESSED_PATH}")

    df = pd.read_csv(PROCESSED_PATH)

    expected_cols = ["Timestamp"] + NUM_FEATURES + CAT_FEATURES + [TARGET]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in processed dataset: {missing}")

    X = df[NUM_FEATURES + CAT_FEATURES].copy()
    y = df[TARGET].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline(steps=[
                ("scaler", StandardScaler())
            ]), NUM_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES),
        ]
    )

    # ✅ MUCH SMALLER THAN RANDOM FOREST ON DISK
    params = {
        "max_depth": 6,
        "learning_rate": 0.08,
        "max_iter": 400,
        "random_state": 42
    }

    model = HistGradientBoostingRegressor(**params)

    pipeline = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("model", model)
    ])

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    with mlflow.start_run(run_name="hgb-regressor-v1"):
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = mean_squared_error(y_test, y_pred) ** 0.5
        r2 = r2_score(y_test, y_pred)

        mlflow.log_params(params)
        mlflow.log_metrics({
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2)
        })

        pred_plot = os.path.join(ARTIFACT_DIR, "pred_vs_actual.png")
        res_plot = os.path.join(ARTIFACT_DIR, "residuals.png")
        plot_pred_vs_actual(y_test.to_numpy(), y_pred, pred_plot)
        plot_residuals(y_test.to_numpy(), y_pred, res_plot)
        mlflow.log_artifact(pred_plot)
        mlflow.log_artifact(res_plot)

        mlflow.sklearn.log_model(
            pipeline,
            "model",
            registered_model_name="ev-energy-regressor"
        )

        joblib.dump(pipeline, MODEL_PATH)

        feature_config = {
            "num_features": NUM_FEATURES,
            "cat_features": CAT_FEATURES,
            "target": TARGET,
            "model_path": MODEL_PATH
        }
        with open(FEATURE_CONFIG_PATH, "w") as f:
            json.dump(feature_config, f, indent=2)

        mlflow.set_tags({
            "environment": "development",
            "model_type": "HistGradientBoostingRegressor",
            "task": "regression",
            "project": "ev-energy-mlops-pipeline"
        })

        print("\n" + "=" * 55)
        print("✅ TRAINING RESULTS (EV ENERGY REGRESSION)")
        print("=" * 55)
        print(f"MAE :  {mae:.4f}")
        print(f"RMSE:  {rmse:.4f}")
        print(f"R2  :  {r2:.4f}")
        print("=" * 55)
        print(f"\nSaved model -> {MODEL_PATH}")
        print(f"Saved config -> {FEATURE_CONFIG_PATH}")
        print("\nMLflow UI:")
        print("  mlflow ui --port 5000")
        print("=" * 55)


if __name__ == "__main__":
    main()
