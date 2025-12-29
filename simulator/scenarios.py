import random
from typing import Dict, Any


def normal_context(vehicle_id: str = "vehicle_001") -> Dict[str, Any]:
    """Generate a realistic EV sensor context (features only)."""
    return {
        "vehicle_id": vehicle_id,
        "Speed_kmh": round(random.uniform(40, 95), 2),
        "Acceleration_ms2": round(random.uniform(0.2, 1.6), 2),
        "Slope_%": round(random.uniform(-2, 8), 2),
        "Temperature_C": round(random.uniform(10, 32), 2),
        "Battery_State_%": round(random.uniform(30, 90), 2),
        "Driving_Mode": random.choice(["eco", "normal", "sport"]),
        "Traffic_Condition": random.choice(["low", "medium", "high"]),
    }


def attach_energy(payload: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """
    Add measured energy consumption to the payload.
    mode:
      - normal: typical range
      - anomaly: abnormally high for same context
      - drift: shifts distributions (speed/mode/traffic) + higher energy
    """
    p = dict(payload)

    if mode == "normal":
        p["Energy_Consumption_kWh"] = round(random.uniform(7.0, 11.5), 2)

    elif mode == "anomaly":
        # keep context similar but energy much higher
        p["Energy_Consumption_kWh"] = round(random.uniform(22, 35), 2)

    elif mode == "drift":
        # shift context distributions to simulate drift
        p["Speed_kmh"] = round(random.uniform(110, 145), 2)
        p["Driving_Mode"] = "sport"
        p["Traffic_Condition"] = "low"
        p["Energy_Consumption_kWh"] = round(random.uniform(18, 30), 2)

    else:
        raise ValueError("mode must be one of: normal, anomaly, drift")

    return p
