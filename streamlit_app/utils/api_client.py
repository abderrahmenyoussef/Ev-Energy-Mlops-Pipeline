"""
API client for EV Energy MLOps API
"""
import requests
from typing import Dict, Any, Optional
import streamlit as st
from config import API_BASE_URL


class EVEnergyAPIClient:
    """Client for interacting with EV Energy API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single prediction"""
        try:
            response = self.session.post(
                f"{self.base_url}/predict",
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Prediction failed: {e}")
            return None
    
    def predict_batch(self, items: list) -> Dict[str, Any]:
        """Make batch predictions"""
        try:
            response = self.session.post(
                f"{self.base_url}/predict/batch",
                json={"items": items},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Batch prediction failed: {e}")
            return None
    
    def check_drift(self) -> Dict[str, Any]:
        """Check for data drift"""
        try:
            response = self.session.get(f"{self.base_url}/drift/check", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Drift check failed: {e}")
            return None
    
    def reset_stream(self, vehicle_id: str = "vehicle_001") -> Dict[str, Any]:
        """Reset streaming state"""
        try:
            response = self.session.post(
                f"{self.base_url}/stream/reset",
                params={"vehicle_id": vehicle_id},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Stream reset failed: {e}")
            return None
    
    def simulate_stream(self, mode: str, duration: int, vehicle_id: str = "vehicle_001") -> Dict[str, Any]:
        """
        Simulate streaming data
        Note: This is a helper that calls predict multiple times to simulate streaming
        """
        import time
        import random
        
        results = []
        
        for i in range(duration):
            # Generate synthetic data based on mode
            data = self._generate_data(mode, i, vehicle_id)
            result = self.predict(data)
            
            if result:
                results.append(result)
            
            time.sleep(1)  # 1 second between requests
        
        return results
    
    def _generate_data(self, mode: str, index: int, vehicle_id: str) -> Dict[str, Any]:
        """Generate synthetic vehicle data for streaming simulation"""
        import random
        
        base_data = {
            "vehicle_id": vehicle_id,
            "Speed_kmh": random.uniform(50, 100),
            "Acceleration_ms2": random.uniform(-1, 1),
            "Slope_%": random.uniform(-5, 5),
            "Temperature_C": random.uniform(15, 25),
            "Battery_State_%": random.uniform(60, 90),
            "Driving_Mode": random.choice(["eco", "normal", "sport"]),
            "Traffic_Condition": random.choice(["low", "medium", "high"]),
        }
        
        # Adjust based on mode
        if mode == "anomaly":
            # Inject anomalies randomly
            if random.random() > 0.6:
                # Add excessive energy consumption
                base_data["Energy_Consumption_kWh"] = random.uniform(15, 25)
            else:
                base_data["Energy_Consumption_kWh"] = random.uniform(8, 12)
        
        elif mode == "drift":
            # Gradually increase features to simulate drift
            drift_factor = 1 + (index * 0.05)
            base_data["Speed_kmh"] *= drift_factor
            base_data["Acceleration_ms2"] *= drift_factor
            base_data["Energy_Consumption_kWh"] = random.uniform(8, 12) * drift_factor
        
        else:  # normal
            base_data["Energy_Consumption_kWh"] = random.uniform(8, 12)
        
        return base_data
