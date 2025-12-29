"""
Manual Prediction Page
"""
import streamlit as st
from utils.auth import require_authentication
from utils.api_client import EVEnergyAPIClient
from config import (
    APP_ICON, FEATURE_RANGES, DRIVING_MODES, TRAFFIC_CONDITIONS
)
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(
    page_title="Manual Prediction",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .prediction-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .metric-container {
        padding: 1rem;
        border-radius: 8px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
    }
    .anomaly-alert {
        padding: 1rem;
        border-radius: 8px;
        background: #dc3545;
        color: white;
        font-weight: bold;
        text-align: center;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    /* HIDE AUDIO PLAYER COMPLETELY */
    audio {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        position: absolute !important;
        left: -9999px !important;
    }
</style>
""", unsafe_allow_html=True)

# Check authentication
require_authentication()

# Initialize API client
if "api_client" not in st.session_state:
    st.session_state.api_client = EVEnergyAPIClient()

# Page header
st.markdown(f"# 📊 Manual Prediction")
st.markdown("Enter vehicle parameters to get energy consumption predictions")
st.markdown("---")

# Prediction form
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Vehicle Parameters")
    
    with st.form("prediction_form"):
        vehicle_id = st.text_input(
            "Vehicle ID",
            value="vehicle_001",
            help="Enter your vehicle identifier"
        )
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            speed = st.slider(
                "Speed (km/h)",
                min_value=FEATURE_RANGES["Speed_kmh"]["min"],
                max_value=FEATURE_RANGES["Speed_kmh"]["max"],
                value=st.session_state.get("speed", FEATURE_RANGES["Speed_kmh"]["default"]),
                step=FEATURE_RANGES["Speed_kmh"]["step"]
            )
            
            acceleration = st.slider(
                "Acceleration (m/s²)",
                min_value=FEATURE_RANGES["Acceleration_ms2"]["min"],
                max_value=FEATURE_RANGES["Acceleration_ms2"]["max"],
                value=st.session_state.get("acceleration", FEATURE_RANGES["Acceleration_ms2"]["default"]),
                step=FEATURE_RANGES["Acceleration_ms2"]["step"]
            )
            
            slope = st.slider(
                "Slope (%)",
                min_value=FEATURE_RANGES["Slope_%"]["min"],
                max_value=FEATURE_RANGES["Slope_%"]["max"],
                value=st.session_state.get("slope", FEATURE_RANGES["Slope_%"]["default"]),
                step=FEATURE_RANGES["Slope_%"]["step"]
            )
        
        with col_b:
            temperature = st.slider(
                "Temperature (°C)",
                min_value=FEATURE_RANGES["Temperature_C"]["min"],
                max_value=FEATURE_RANGES["Temperature_C"]["max"],
                value=st.session_state.get("temperature", FEATURE_RANGES["Temperature_C"]["default"]),
                step=FEATURE_RANGES["Temperature_C"]["step"]
            )
            
            battery_state = st.slider(
                "Battery State (%)",
                min_value=FEATURE_RANGES["Battery_State_%"]["min"],
                max_value=FEATURE_RANGES["Battery_State_%"]["max"],
                value=st.session_state.get("battery", FEATURE_RANGES["Battery_State_%"]["default"]),
                step=FEATURE_RANGES["Battery_State_%"]["step"]
            )
            
            driving_mode = st.selectbox(
                "Driving Mode", 
                DRIVING_MODES,
                index=DRIVING_MODES.index(st.session_state.get("driving_mode", DRIVING_MODES[0]))
            )
        
        traffic_condition = st.selectbox(
            "Traffic Condition", 
            TRAFFIC_CONDITIONS,
            index=TRAFFIC_CONDITIONS.index(st.session_state.get("traffic", TRAFFIC_CONDITIONS[0]))
        )
        
        actual_consumption = st.number_input(
            "Actual Energy Consumption (kWh) - Optional",
            min_value=0.0,
            max_value=50.0,
            value=0.0,
            step=0.1,
            help="Leave as 0 if you don't have actual consumption data"
        )
        
        submitted = st.form_submit_button("🔮 Predict", width='stretch')

with col2:
    st.markdown("### Quick Presets")
    
    if st.button("🌆 City Driving", width='stretch'):
        st.session_state.speed = 40
        st.session_state.acceleration = 1.0
        st.session_state.slope = 0
        st.session_state.temperature = 20
        st.session_state.battery = 80
        st.session_state.driving_mode = "eco"
        st.session_state.traffic = "medium"
        st.rerun()
    
    if st.button("🛣️ Highway", width='stretch'):
        st.session_state.speed = 110
        st.session_state.acceleration = 0.5
        st.session_state.slope = 0
        st.session_state.temperature = 22
        st.session_state.battery = 75
        st.session_state.driving_mode = "normal"
        st.session_state.traffic = "low"
        st.rerun()
    
    if st.button("⛰️ Mountain", width='stretch'):
        st.session_state.speed = 60
        st.session_state.acceleration = 1.5
        st.session_state.slope = 8
        st.session_state.temperature = 15
        st.session_state.battery = 70
        st.session_state.driving_mode = "sport"
        st.session_state.traffic = "low"
        st.rerun()
    
    if st.button("🌧️ Bad Weather", width='stretch'):
        st.session_state.speed = 50
        st.session_state.acceleration = 0.8
        st.session_state.slope = 0
        st.session_state.temperature = 5
        st.session_state.battery = 65
        st.session_state.driving_mode = "eco"
        st.session_state.traffic = "high"
        st.rerun()

# Make prediction
if submitted:
    # Prepare data
    data = {
        "vehicle_id": vehicle_id,
        "Speed_kmh": speed,
        "Acceleration_ms2": acceleration,
        "Slope_%": slope,
        "Temperature_C": temperature,
        "Battery_State_%": battery_state,
        "Driving_Mode": driving_mode,
        "Traffic_Condition": traffic_condition,
    }
    
    if actual_consumption > 0:
        data["Energy_Consumption_kWh"] = actual_consumption
    
    with st.spinner("Making prediction..."):
        result = st.session_state.api_client.predict(data)
    
    if result:
        st.markdown("---")
        st.markdown("## 📊 Prediction Results")
        
        # Display results
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <h3>{result['predicted_kwh']:.2f} kWh</h3>
                <p>Predicted Consumption</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if result['actual_kwh']:
                st.markdown(f"""
                <div class="metric-container">
                    <h3>{result['actual_kwh']:.2f} kWh</h3>
                    <p>Actual Consumption</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No actual data provided")
        
        with col3:
            if result['residual_kwh'] is not None:
                color = "red" if result['is_anomaly'] else "green"
                st.markdown(f"""
                <div class="metric-container" style="background: {color};">
                    <h3>{result['residual_kwh']:.2f} kWh</h3>
                    <p>Residual</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("N/A")
        
        with col4:
            if result['error_pct'] is not None:
                st.markdown(f"""
                <div class="metric-container">
                    <h3>{result['error_pct']:.1f}%</h3>
                    <p>Error Percentage</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("N/A")
        
        # Anomaly alert
        if result['is_anomaly']:
            st.markdown("""
            <div class="anomaly-alert">
                ⚠️ ANOMALY DETECTED! Energy consumption is significantly higher than expected!
            </div>
            """, unsafe_allow_html=True)
            
            if result['alert']:
                st.error("🚨 ALERT! Multiple consecutive anomalies detected!")
        else:
            st.success("✅ No anomaly detected. Energy consumption is within normal range.")
        
        # Threshold information
        st.markdown("### 📏 Detection Thresholds")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Residual Threshold",
                f"{result['thresholds']['residual_threshold_kwh_p95']:.2f} kWh"
            )
        
        with col2:
            st.metric(
                "Error % Threshold",
                f"{result['thresholds']['error_pct_threshold_p95']:.1f}%"
            )
        
        # Visualization
        st.markdown("### 📈 Visualization")
        
        if result['actual_kwh']:
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=['Predicted', 'Actual'],
                y=[result['predicted_kwh'], result['actual_kwh']],
                marker_color=['#667eea', '#dc3545' if result['is_anomaly'] else '#28a745'],
                text=[f"{result['predicted_kwh']:.2f}", f"{result['actual_kwh']:.2f}"],
                textposition='auto',
            ))
            
            fig.update_layout(
                title="Predicted vs Actual Energy Consumption",
                yaxis_title="Energy (kWh)",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Prediction Info")
    st.info("""
    This page allows you to manually enter vehicle parameters and get instant predictions.
    
    **Features:**
    - Real-time prediction
    - Anomaly detection
    - Visual feedback
    - Alert system
    """)
