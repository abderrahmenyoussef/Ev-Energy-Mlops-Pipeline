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
      - normal  : normal driving + normal energy
      - anomaly : same context but energy abnormally high
      - drift   : shift distributions of MONITORED features (so drift/check becomes true)
    """
    p = dict(payload)

    if mode == "normal":
        # tighten a bit to reduce random anomalies
        p["Energy_Consumption_kWh"] = round(random.uniform(8.0, 10.8), 2)

    elif mode == "anomaly":
        # keep context similar but energy much higher
        p["Energy_Consumption_kWh"] = round(random.uniform(22, 35), 2)

    elif mode == "drift":
        # REAL drift: shift multiple sensor distributions, not only speed
        p["Speed_kmh"] = round(random.uniform(160, 185), 2)
        p["Acceleration_ms2"] = round(random.uniform(1.4, 2.2), 2)
        p["Slope_%"] = round(random.uniform(10, 18), 2)
        p["Temperature_C"] = round(random.uniform(38, 48), 2)
        p["Battery_State_%"] = round(random.uniform(15, 30), 2)
        p["Driving_Mode"] = "sport"
        p["Traffic_Condition"] = "high"

        # energy can be higher, but drift is detected via sensors
        p["Energy_Consumption_kWh"] = round(random.uniform(18, 30), 2)

    else:
        raise ValueError("mode must be one of: normal, anomaly, drift")

    return p
