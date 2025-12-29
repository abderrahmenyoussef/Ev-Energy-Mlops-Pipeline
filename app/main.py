from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.models import (
    HealthResponse,
    EVSensorReading,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    DriftCheckResponse,
)
from app.utils import ArtifactStore
from app.drift_detect import compute_drift_scores

app = FastAPI(title="EV Energy MLOps Pipeline API", version="0.1.0")

store = ArtifactStore()

# Drift buffer in RAM (last N points)
RECENT_BUFFER_SIZE = 200
recent_buffer: Dict[str, List[float]] = {
    "Speed_kmh": [],
    "Acceleration_ms2": [],
    "Slope_%": [],
    "Temperature_C": [],
    "Battery_State_%": [],
    "Energy_Consumption_kWh": [],
}

MONITORED_DRIFT_FEATURES = [
    "Speed_kmh",
    "Acceleration_ms2",
    "Slope_%",
    "Temperature_C",
    "Battery_State_%",
    "Energy_Consumption_kWh",
]


@app.on_event("startup")
def startup_event():
    store.load()


@app.get("/")
def root():
    return {"message": "EV Energy MLOps Pipeline API is running."}


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        model_loaded=store.model_loaded,
        model_path=store.model_path,
    )


def _push(buf_key: str, value: Any) -> None:
    if value is None:
        return
    recent_buffer[buf_key].append(float(value))
    if len(recent_buffer[buf_key]) > RECENT_BUFFER_SIZE:
        recent_buffer[buf_key] = recent_buffer[buf_key][-RECENT_BUFFER_SIZE:]


@app.post("/predict", response_model=PredictionResponse)
def predict(item: EVSensorReading):
    payload = item.model_dump(by_alias=True)

    # Update drift buffer (for drift/check)
    _push("Speed_kmh", payload.get("Speed_kmh"))
    _push("Acceleration_ms2", payload.get("Acceleration_ms2"))
    _push("Slope_%", payload.get("Slope_%"))
    _push("Temperature_C", payload.get("Temperature_C"))
    _push("Battery_State_%", payload.get("Battery_State_%"))
    _push("Energy_Consumption_kWh", payload.get("Energy_Consumption_kWh"))

    # Predict
    vehicle_id = item.vehicle_id or "vehicle_001"
    X = store.build_features_df(payload)
    predicted = store.predict_kwh(X)

    # Anomaly detection if actual energy is provided
    actual = payload.get("Energy_Consumption_kWh")
    is_anom, alert, residual, err_pct = store.detect_anomaly(
        vehicle_id=vehicle_id,
        predicted_kwh=predicted,
        actual_kwh=actual,
    )

    return PredictionResponse(
        vehicle_id=vehicle_id,
        predicted_kwh=predicted,
        actual_kwh=actual,
        residual_kwh=residual,
        error_pct=err_pct,
        is_anomaly=is_anom,
        alert=alert,
        thresholds=store.get_thresholds_payload(),
    )


@app.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(req: BatchPredictionRequest):
    results: List[PredictionResponse] = []
    for item in req.items:
        results.append(predict(item))
    return BatchPredictionResponse(results=results)


@app.get("/drift/check", response_model=DriftCheckResponse)
def drift_check():
    feature_scores, drift_score = compute_drift_scores(
        baseline_stats=store.baseline_stats,
        recent_batch=recent_buffer,
        monitored_features=MONITORED_DRIFT_FEATURES,
    )

    drift_detected = drift_score >= 2.0  # threshold you can tune
    msg = f"Drift detected (score={drift_score:.2f})." if drift_detected else f"No drift (score={drift_score:.2f})."

    return DriftCheckResponse(
        drift_detected=drift_detected,
        drift_score=float(drift_score),
        feature_scores=feature_scores,
        message=msg,
    )


@app.post("/drift/alert")
def drift_alert():
    res = drift_check()
    if res.drift_detected:
        return JSONResponse(
            status_code=200,
            content={
                "alert": True,
                "message": "🚨 Drift detected! Consider retraining the model.",
                "details": res.model_dump(),
            },
        )
    return {"alert": False, "message": "No drift detected.", "details": res.model_dump()}
