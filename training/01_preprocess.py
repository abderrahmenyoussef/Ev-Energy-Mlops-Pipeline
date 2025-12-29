import os
import pandas as pd

RAW_PATH = "data/raw/EV_Energy_Consumption_Dataset.csv"
OUT_PATH = "data/processed/ev_energy_processed.csv"

# Features sélectionnées (scope volontairement réduit)
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
KEEP_COLS = ["Timestamp"] + NUM_FEATURES + CAT_FEATURES + [TARGET]


def main() -> None:
    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(f"Raw dataset not found: {RAW_PATH}")

    df = pd.read_csv(RAW_PATH)

    # --- Basic checks
    missing_cols = [c for c in KEEP_COLS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing expected columns in CSV: {missing_cols}")

    # --- Parse Timestamp (safe)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    # Keep only needed columns
    df = df[KEEP_COLS].copy()

    # Drop rows with missing target
    df = df.dropna(subset=[TARGET])

    # Clean categorical strings
    for c in CAT_FEATURES:
        df[c] = df[c].astype(str).str.strip().str.lower()

    # Handle missing values:
    # - numeric: fill with median
    for c in NUM_FEATURES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df[c] = df[c].fillna(df[c].median())

    # - categorical: fill with mode
    for c in CAT_FEATURES:
        mode_val = df[c].mode(dropna=True)
        fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "unknown"
        df[c] = df[c].replace({"nan": None}).fillna(fill_val)

    # Drop rows with invalid timestamps (optional but clean)
    df = df.dropna(subset=["Timestamp"])

    # Final safety: remove infinities
    df = df.replace([float("inf"), float("-inf")], pd.NA).dropna()

    # Save
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print("✅ Preprocessing done!")
    print(f"Saved processed dataset -> {OUT_PATH}")
    print(f"Shape: {df.shape}")
    print("Columns:", list(df.columns))


if __name__ == "__main__":
    main()
