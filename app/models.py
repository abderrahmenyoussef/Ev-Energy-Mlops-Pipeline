from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str


class EVSensorReading(BaseModel):
    # metadata
    vehicle_id: Optional[str] = "vehicle_001"
    timestamp: Optional[str] = None

    # model features
    Speed_kmh: float
    Acceleration_ms2: float
    Slope_: float = Field(alias="Slope_%")
    Temperature_C: float
    Battery_State_: float = Field(alias="Battery_State_%")
    Driving_Mode: str
    Traffic_Condition: str

    # ✅ IMPORTANT: real measured energy from the "sensor"
    Energy_Consumption_kWh: Optional[float] = None

    class Config:
        populate_by_name = True


class PredictionResponse(BaseModel):
    vehicle_id: str
    predicted_kwh: float
    actual_kwh: Optional[float] = None
    residual_kwh: Optional[float] = None
    error_pct: Optional[float] = None
    is_anomaly: bool
    alert: bool
    thresholds: Dict[str, Any]


class BatchPredictionRequest(BaseModel):
    items: List[EVSensorReading]


class BatchPredictionResponse(BaseModel):
    results: List[PredictionResponse]


class DriftCheckResponse(BaseModel):
    drift_detected: bool
    drift_score: float
    feature_scores: Dict[str, float]
    message: str
