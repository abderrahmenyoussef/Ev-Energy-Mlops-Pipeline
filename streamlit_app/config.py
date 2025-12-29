"""
Configuration file for the Streamlit app
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration - REQUIRED from .env
API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    raise ValueError("API_BASE_URL must be set in .env file")

# Database Configuration - REQUIRED from .env (db4free.net)
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None,
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Validate all required DB config
for key, value in DB_CONFIG.items():
    if value is None:
        raise ValueError(f"DB_{key.upper()} must be set in .env file")

# App Configuration - Optional with defaults
APP_TITLE = os.getenv("APP_TITLE", "⚡ EV Energy Monitor")
APP_ICON = os.getenv("APP_ICON", "⚡")

# Streaming Configuration
STREAMING_MODES = {
    "normal": {
        "name": "🟢 Normal Mode",
        "description": "Standard driving conditions",
        "color": "#28a745"
    },
    "anomaly": {
        "name": "🔴 Anomaly Mode",
        "description": "Inject energy consumption anomalies",
        "color": "#dc3545"
    },
    "drift": {
        "name": "🟠 Drift Mode",
        "description": "Simulate gradual distribution shift",
        "color": "#fd7e14"
    }
}

# Vehicle Features Ranges
FEATURE_RANGES = {
    "Speed_kmh": {"min": 0, "max": 150, "default": 60, "step": 5},
    "Acceleration_ms2": {"min": -5.0, "max": 5.0, "default": 0.0, "step": 0.1},
    "Slope_%": {"min": -15, "max": 15, "default": 0, "step": 1},
    "Temperature_C": {"min": -20, "max": 45, "default": 20, "step": 1},
    "Battery_State_%": {"min": 0, "max": 100, "default": 80, "step": 5},
}

DRIVING_MODES = ["eco", "normal", "sport"]
TRAFFIC_CONDITIONS = ["low", "medium", "high"]

# Alert Settings
ALERT_THRESHOLD_CONSECUTIVE = 3  # Number of consecutive anomalies to trigger alert
ALERT_SOUND_DURATION = 2  # seconds
