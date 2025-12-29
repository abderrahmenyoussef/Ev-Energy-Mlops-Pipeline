"""
Dashboard Page
"""
import streamlit as st
from utils.auth import require_authentication
from utils.api_client import EVEnergyAPIClient
from config import APP_ICON
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(
    page_title="Dashboard",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .dashboard-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .kpi-card {
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .drift-warning {
        padding: 1rem;
        border-radius: 8px;
        background: #fd7e14;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Check authentication
require_authentication()

# Initialize
if "api_client" not in st.session_state:
    st.session_state.api_client = EVEnergyAPIClient()

# Page header
st.markdown("# 📈 Analytics Dashboard")
st.markdown("Comprehensive monitoring and analytics for your electric vehicle")
st.markdown("---")

# KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_predictions = len(st.session_state.get("streaming_data", []))
    st.markdown(f"""
    <div class="kpi-card">
        <h2>{total_predictions}</h2>
        <p>Total Predictions</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    anomaly_count = st.session_state.get("anomaly_count", 0)
    st.markdown(f"""
    <div class="kpi-card">
        <h2>{anomaly_count}</h2>
        <p>Anomalies Detected</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    anomaly_rate = (anomaly_count / total_predictions * 100) if total_predictions > 0 else 0
    st.markdown(f"""
    <div class="kpi-card">
        <h2>{anomaly_rate:.1f}%</h2>
        <p>Anomaly Rate</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <h2>{"✅" if not st.session_state.get("alert_triggered", False) else "⚠️"}</h2>
        <p>System Status</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Drift Detection
st.markdown("## 🔍 Drift Detection")

col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🔄 Check for Data Drift", width='stretch'):
        with st.spinner("Analyzing data distribution..."):
            drift_result = st.session_state.api_client.check_drift()
        
        if drift_result:
            st.session_state.drift_result = drift_result

if "drift_result" in st.session_state:
    drift = st.session_state.drift_result
    
    with col2:
        if drift["drift_detected"]:
            st.markdown(f"""
            <div class="drift-warning">
                ⚠️ DRIFT DETECTED!<br>
                Score: {drift['drift_score']:.2f}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"✅ No drift detected\nScore: {drift['drift_score']:.2f}")
    
    # Feature drift scores
    st.markdown("### Feature Drift Scores")
    
    if drift.get("feature_scores"):
        df_drift = pd.DataFrame({
            "Feature": list(drift["feature_scores"].keys()),
            "Z-Score": list(drift["feature_scores"].values())
        })
        
        fig = go.Figure(go.Bar(
            x=df_drift["Feature"],
            y=df_drift["Z-Score"],
            marker_color=['#dc3545' if x > 2.0 else '#28a745' for x in df_drift["Z-Score"]],
            text=df_drift["Z-Score"].round(2),
            textposition='auto',
        ))
        
        fig.add_hline(y=2.0, line_dash="dash", line_color="red", 
                      annotation_text="Drift Threshold (2.0)")
        
        fig.update_layout(
            title="Feature Drift Analysis",
            xaxis_title="Feature",
            yaxis_title="Z-Score",
            height=400
        )
        
        st.plotly_chart(fig, width='stretch')

st.markdown("---")

# Historical Data Analysis
st.markdown("## 📊 Historical Data Analysis")

if st.session_state.get("streaming_data"):
    df = pd.DataFrame(st.session_state.streaming_data)
    
    # Time series analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Energy Consumption Trends")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['predicted_kwh'],
            name='Predicted',
            line=dict(color='#667eea', width=2)
        ))
        
        if 'actual_kwh' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['actual_kwh'],
                name='Actual',
                line=dict(color='#28a745', width=2)
            ))
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Energy (kWh)",
            height=350,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("### Error Distribution")
        
        if 'error_pct' in df.columns:
            fig = go.Figure(go.Histogram(
                x=df['error_pct'],
                nbinsx=20,
                marker_color='#667eea'
            ))
            
            fig.update_layout(
                xaxis_title="Error Percentage (%)",
                yaxis_title="Frequency",
                height=350
            )
            
            st.plotly_chart(fig, width='stretch')
    
    # Anomaly timeline
    st.markdown("### Anomaly Timeline")
    
    anomalies_over_time = df['is_anomaly'].rolling(window=5).sum()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=anomalies_over_time,
        fill='tozeroy',
        name='Anomalies (5-point rolling)',
        line=dict(color='#dc3545')
    ))
    
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Anomaly Count",
        height=350
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Statistics table
    st.markdown("### Summary Statistics")
    
    stats_data = {
        "Metric": [
            "Mean Predicted (kWh)",
            "Mean Actual (kWh)",
            "Std Dev",
            "Max Error (%)",
            "Min Error (%)",
        ],
        "Value": [
            f"{df['predicted_kwh'].mean():.2f}",
            f"{df['actual_kwh'].mean():.2f}" if 'actual_kwh' in df.columns else "N/A",
            f"{df['predicted_kwh'].std():.2f}",
            f"{df['error_pct'].max():.2f}" if 'error_pct' in df.columns else "N/A",
            f"{df['error_pct'].min():.2f}" if 'error_pct' in df.columns else "N/A",
        ]
    }
    
    st.dataframe(pd.DataFrame(stats_data), width='stretch', hide_index=True)
    
    # Data export
    st.markdown("### 📥 Export Data")
    
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"ev_energy_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

else:
    st.info("No streaming data available. Start a streaming session to see analytics.")
    
    if st.button("📡 Start Streaming", width='stretch'):
        st.switch_page("pages/3_📡_Real_Time_Streaming.py")

st.markdown("---")

# API Health
st.markdown("## 🏥 API Health Status")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Check API Health", width='stretch'):
        health = st.session_state.api_client.health_check()
        st.session_state.api_health = health

if "api_health" in st.session_state:
    health = st.session_state.api_health
    
    with col2:
        if health.get("status") == "ok":
            st.success("✅ API is healthy")
        else:
            st.error("❌ API is down")
    
    with col3:
        st.info(f"Model: {'Loaded ✅' if health.get('model_loaded') else 'Not Loaded ❌'}")

# Sidebar
with st.sidebar:
    st.markdown("### 📈 Dashboard Options")
    
    st.markdown("#### Quick Actions")
    
    if st.button("🔄 Refresh Data", width='stretch'):
        st.rerun()
    
    if st.button("🗑️ Clear All Data", width='stretch'):
        st.session_state.streaming_data = []
        st.session_state.anomaly_count = 0
        st.session_state.alert_triggered = False
        st.success("Data cleared!")
        st.rerun()
    
    st.markdown("---")
    
    st.info("""
    **Dashboard Features:**
    - Real-time KPIs
    - Drift detection
    - Historical analysis
    - Data export
    - API monitoring
    """)
