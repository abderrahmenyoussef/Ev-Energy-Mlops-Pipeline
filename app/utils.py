import json
import os
from collections import deque
from typing import Dict, Any, Tuple, Optional

import joblib
import numpy as np
import pandas as pd


class ArtifactStore:
    def __init__(self, model_dir: str = "model"):
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "ev_energy_model.pkl")
        self.feature_config_path = os.path.join(model_dir, "feature_config.json")
        self.anomaly_config_path = os.path.join(model_dir, "anomaly_config.json")
        self.baseline_stats_path = os.path.join(model_dir, "baseline_stats.json")

        self.pipeline = None
        self.feature_config: Dict[str, Any] = {}
        self.anomaly_config: Dict[str, Any] = {}
        self.baseline_stats: Dict[str, Any] = {}

        # streaming memory: per vehicle -> deque of bool anomalies
        self._anomaly_history: Dict[str, deque] = {}

    def load(self) -> None:
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        self.pipeline = joblib.load(self.model_path)

        with open(self.feature_config_path, "r") as f:
            self.feature_config = json.load(f)
        with open(self.anomaly_config_path, "r") as f:
            self.anomaly_config = json.load(f)
        with open(self.baseline_stats_path, "r") as f:
            self.baseline_stats = json.load(f)

    @property
    def model_loaded(self) -> bool:
        return self.pipeline is not None

    def _get_vehicle_deque(self, vehicle_id: str) -> deque:
        window = int(self.anomaly_config.get("alert_window_size", 20))
        if vehicle_id not in self._anomaly_history:
            self._anomaly_history[vehicle_id] = deque(maxlen=window)
        return self._anomaly_history[vehicle_id]

    def build_features_df(self, item_dict: Dict[str, Any]) -> pd.DataFrame:
        num_features = self.feature_config["num_features"]
        cat_features = self.feature_config["cat_features"]
        cols = num_features + cat_features

        # Ensure we only keep expected fields
        row = {c: item_dict.get(c) for c in cols}
        return pd.DataFrame([row], columns=cols)

    def predict_kwh(self, features_df: pd.DataFrame) -> float:
        pred = float(self.pipeline.predict(features_df)[0])
        return pred

    def detect_anomaly(
        self,
        vehicle_id: str,
        predicted_kwh: float,
        actual_kwh: Optional[float],
    ) -> Tuple[bool, bool, Optional[float], Optional[float]]:
        """
        Returns: is_anomaly, alert, residual_kwh, error_pct
        If actual_kwh is None, we can't compute anomaly -> is_anomaly False.
        """
        if actual_kwh is None:
            return False, False, None, None

        residual = float(actual_kwh - predicted_kwh)
        error_pct = float((residual / (abs(predicted_kwh) + 1e-6)) * 100.0)

        thr_res = float(self.anomaly_config["residual_threshold_kwh_p95"])
        thr_pct = float(self.anomaly_config["error_pct_threshold_p95"])

        is_anomaly = (residual > thr_res) or (error_pct > thr_pct)

        # Persistent alert logic
        history = self._get_vehicle_deque(vehicle_id)
        history.append(bool(is_anomaly))

        min_in_window = int(self.anomaly_config.get("alert_min_anomalies_in_window", 10))
        consecutive = int(self.anomaly_config.get("alert_consecutive_anomalies", 5))

        # count anomalies in current window
        count_anom = sum(history)

        # consecutive anomalies check
        consec = 0
        for v in reversed(history):
            if v:
                consec += 1
            else:
                break

        alert = (count_anom >= min_in_window) or (consec >= consecutive)
        return is_anomaly, alert, residual, error_pct

    def get_thresholds_payload(self) -> Dict[str, Any]:
        return {
            "residual_threshold_kwh_p95": self.anomaly_config["residual_threshold_kwh_p95"],
            "error_pct_threshold_p95": self.anomaly_config["error_pct_threshold_p95"],
            "window_size": self.anomaly_config.get("alert_window_size", 20),
            "min_anomalies_in_window": self.anomaly_config.get("alert_min_anomalies_in_window", 10),
            "consecutive_anomalies": self.anomaly_config.get("alert_consecutive_anomalies", 5),
        }
