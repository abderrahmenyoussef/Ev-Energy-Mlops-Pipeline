"""
Real-Time Streaming Page - Enhanced Version
"""
import streamlit as st
from utils.auth import require_authentication
from utils.api_client import EVEnergyAPIClient
from config import APP_ICON, STREAMING_MODES
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from datetime import datetime
import numpy as np

st.set_page_config(
    page_title="Real-Time Streaming",
    page_icon="📡",
    layout="wide"
)

# Custom CSS + Hidden Audio Player
st.markdown("""
<style>
    .streaming-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .connection-card {
        padding: 2rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin: 2rem 0;
    }
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background: #28a745;
        border-radius: 50%;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .alert-box {
        padding: 1.5rem;
        border-radius: 10px;
        background: #dc3545;
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
        animation: shake 0.5s infinite;
    }
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    .stats-box {
        padding: 1rem;
        border-radius: 8px;
        background: #f8f9fa;
        border-left: 4px solid #667eea;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 8px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
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

# Initialize
if "api_client" not in st.session_state:
    st.session_state.api_client = EVEnergyAPIClient()

if "streaming_active" not in st.session_state:
    st.session_state.streaming_active = False

if "streaming_data" not in st.session_state:
    st.session_state.streaming_data = []

if "anomaly_count" not in st.session_state:
    st.session_state.anomaly_count = 0

if "alert_triggered" not in st.session_state:
    st.session_state.alert_triggered = False

if "stream_finished" not in st.session_state:
    st.session_state.stream_finished = False

# Page header
st.markdown('<h1 class="streaming-header">📡 Real-Time Streaming</h1>', unsafe_allow_html=True)
st.markdown("Connect to your Electric Vehicle and monitor energy consumption in real-time")
st.markdown("---")

# Connection panel
if not st.session_state.streaming_active and not st.session_state.stream_finished:
    st.markdown("""
    <div class="connection-card">
        <h2>🚗 Connect to Your Electric Vehicle</h2>
        <p>Configure streaming parameters and start monitoring</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### ⚙️ Streaming Configuration")
        
        vehicle_id = st.text_input(
            "Vehicle ID",
            value="vehicle_001",
            help="Enter your vehicle identifier"
        )
        
        # Mode selection
        st.markdown("#### Select Streaming Mode")
        mode_cols = st.columns(3)
        
        selected_mode = None
        for idx, (mode_key, mode_info) in enumerate(STREAMING_MODES.items()):
            with mode_cols[idx]:
                if st.button(
                    f"{mode_info['name']}\n{mode_info['description']}",
                    width='stretch',
                    key=f"mode_{mode_key}"
                ):
                    selected_mode = mode_key
        
        if "selected_mode" not in st.session_state:
            st.session_state.selected_mode = "normal"
        
        if selected_mode:
            st.session_state.selected_mode = selected_mode
        
        # Display selected mode
        mode_info = STREAMING_MODES[st.session_state.selected_mode]
        st.info(f"Selected Mode: {mode_info['name']}")
        
        # Duration
        duration = st.slider(
            "Streaming Duration (seconds)",
            min_value=10,
            max_value=120,
            value=30,
            step=5,
            help="How long to stream data"
        )
        
        # Update rate
        update_rate = st.slider(
            "Update Rate (seconds)",
            min_value=1,
            max_value=5,
            value=1,
            help="Time between updates"
        )
        
        # Start button
        if st.button("🚀 Start Streaming", width='stretch', type="primary"):
            st.session_state.streaming_active = True
            st.session_state.vehicle_id = vehicle_id
            st.session_state.duration = duration
            st.session_state.update_rate = update_rate
            st.session_state.streaming_data = []
            st.session_state.anomaly_count = 0
            st.session_state.alert_triggered = False
            st.session_state.stream_finished = False
            st.session_state.start_time = time.time()
            st.rerun()
    
    with col2:
        st.markdown("### 📋 Instructions")
        st.markdown("""
        1. **Enter Vehicle ID**: Your unique vehicle identifier
        2. **Select Mode**: 
           - 🟢 Normal: Standard operation
           - 🔴 Anomaly: Test anomaly detection
           - 🟠 Drift: Simulate data drift
        3. **Set Duration**: How long to stream
        4. **Start**: Begin real-time monitoring
        
        ⚠️ **Important**: Reset stream after each scenario!
        """)
        
        st.markdown("### 🔧 Quick Actions")
        if st.button("🔄 Reset Stream", width='stretch'):
            result = st.session_state.api_client.reset_stream(vehicle_id)
            if result:
                st.success("✅ Stream reset successfully!")
                time.sleep(1)
                st.rerun()

elif st.session_state.streaming_active:
    # Streaming active
    st.markdown(f"""
    <div style='text-align: center; padding: 1rem; background: #28a745; color: white; border-radius: 10px;'>
        <span class="live-indicator"></span> <strong>LIVE STREAMING</strong> - {st.session_state.selected_mode.upper()} MODE
    </div>
    """, unsafe_allow_html=True)
    
    # Stop button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⏹️ Stop Streaming", width='stretch', type="secondary"):
            st.session_state.streaming_active = False
            st.session_state.stream_finished = True
            st.rerun()
    
    st.markdown("---")
    
    # Real-time stats
    col1, col2, col3, col4 = st.columns(4)
    
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, st.session_state.duration - elapsed)
    
    with col1:
        st.metric("⏱️ Elapsed", f"{int(elapsed)}s")
    
    with col2:
        st.metric("⏳ Remaining", f"{int(remaining)}s")
    
    with col3:
        st.metric("📊 Data Points", len(st.session_state.streaming_data))
    
    with col4:
        st.metric("⚠️ Anomalies", st.session_state.anomaly_count)
    
    # Alert display
    if st.session_state.alert_triggered:
        st.markdown("""
        <div class="alert-box">
            🚨 ALERT! MULTIPLE ANOMALIES DETECTED! 🚨
        </div>
        """, unsafe_allow_html=True)
    
    # Streaming loop
    if remaining > 0:
        # Generate new data point
        import random
        
        # Simulate data based on mode
        data_point = {
            "timestamp": datetime.now(),
            "vehicle_id": st.session_state.vehicle_id,
            "Speed_kmh": random.uniform(50, 100),
            "Acceleration_ms2": random.uniform(-1, 1),
            "Slope_%": random.uniform(-5, 5),
            "Temperature_C": random.uniform(15, 25),
            "Battery_State_%": random.uniform(60, 90),
            "Driving_Mode": random.choice(["eco", "normal", "sport"]),
            "Traffic_Condition": random.choice(["low", "medium", "high"]),
        }
        
        # Adjust based on mode
        mode = st.session_state.selected_mode
        if mode == "anomaly":
            if random.random() > 0.6:
                data_point["Energy_Consumption_kWh"] = random.uniform(15, 25)
            else:
                data_point["Energy_Consumption_kWh"] = random.uniform(8, 12)
        elif mode == "drift":
            drift_factor = 1 + (elapsed * 0.05)
            data_point["Speed_kmh"] *= drift_factor
            data_point["Energy_Consumption_kWh"] = random.uniform(8, 12) * drift_factor
        else:
            data_point["Energy_Consumption_kWh"] = random.uniform(8, 12)
        
        # Convert datetime to ISO string for JSON serialization
        timestamp = data_point["timestamp"]
        data_point["timestamp"] = timestamp.isoformat()
        
        # Make prediction
        result = st.session_state.api_client.predict(data_point)
        
        if result:
            result["timestamp"] = timestamp
            st.session_state.streaming_data.append(result)
            
            if result["is_anomaly"]:
                st.session_state.anomaly_count += 1
            
            if result["alert"]:
                st.session_state.alert_triggered = True
            
            # Create two columns for charts and data
            col_chart, col_data = st.columns([2, 1])
            
            with col_chart:
                st.markdown("### 📈 Live Visualization")
                
                # Update charts
                df = pd.DataFrame(st.session_state.streaming_data)
                
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=(
                        'Energy Consumption Over Time',
                        'Latest Prediction',
                        'Anomaly Detection',
                        'Error Percentage'
                    )
                )
                
                # Chart 1: Time series
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['predicted_kwh'],
                        name='Predicted',
                        line=dict(color='#667eea', width=2)
                    ),
                    row=1, col=1
                )
                
                if 'actual_kwh' in df.columns and df['actual_kwh'].notna().any():
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df['actual_kwh'],
                            name='Actual',
                            line=dict(color='#28a745', width=2)
                        ),
                        row=1, col=1
                    )
                
                # Chart 2: Latest comparison
                if result.get('actual_kwh'):
                    fig.add_trace(
                        go.Bar(
                            x=['Predicted', 'Actual'],
                            y=[result['predicted_kwh'], result['actual_kwh']],
                            marker_color=['#667eea', '#dc3545' if result['is_anomaly'] else '#28a745']
                        ),
                        row=1, col=2
                    )
                
                # Chart 3: Anomalies
                colors = ['#dc3545' if x else '#28a745' for x in df['is_anomaly']]
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['is_anomaly'].astype(int),
                        mode='markers',
                        marker=dict(size=10, color=colors),
                        name='Anomalies',
                        showlegend=False
                    ),
                    row=2, col=1
                )
                
                # Chart 4: Error percentage
                if 'error_pct' in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df['error_pct'],
                            fill='tozeroy',
                            name='Error %',
                            line=dict(color='#fd7e14')
                        ),
                        row=2, col=2
                    )
                
                fig.update_layout(height=600, showlegend=True)
                st.plotly_chart(fig, width='stretch')
            
            with col_data:
                st.markdown("### 📊 Latest Data Points")
                
                # Show last 5 data points
                recent_data = st.session_state.streaming_data[-5:]
                for i, point in enumerate(reversed(recent_data)):
                    color = "#ffe6e6" if point['is_anomaly'] else "#e6ffe6"
                    st.markdown(f"""
                    <div style='background: {color}; padding: 0.5rem; border-radius: 5px; margin-bottom: 0.5rem;'>
                        <strong>Point #{len(st.session_state.streaming_data) - i}</strong><br/>
                        Predicted: {point['predicted_kwh']:.2f} kWh<br/>
                        {'⚠️ ANOMALY' if point['is_anomaly'] else '✅ Normal'}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Wait for next update
        time.sleep(st.session_state.update_rate)
        st.rerun()
    
    else:
        # Streaming finished
        st.session_state.streaming_active = False
        st.session_state.stream_finished = True
        st.rerun()

elif st.session_state.stream_finished:
    # Show final results like manual prediction
    st.success("✅ Streaming completed!")
    
    st.markdown("---")
    st.markdown("## 📊 Final Results & Analysis")
    
    if st.session_state.streaming_data:
        df = pd.DataFrame(st.session_state.streaming_data)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        avg_predicted = df['predicted_kwh'].mean()
        avg_actual = df['actual_kwh'].mean() if 'actual_kwh' in df.columns and df['actual_kwh'].notna().any() else None
        total_anomalies = df['is_anomaly'].sum()
        anomaly_rate = (total_anomalies / len(df) * 100) if len(df) > 0 else 0
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{avg_predicted:.2f} kWh</h3>
                <p>Average Predicted</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if avg_actual:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{avg_actual:.2f} kWh</h3>
                    <p>Average Actual</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{len(df)}</h3>
                    <p>Total Points</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card" style="background: {'#dc3545' if total_anomalies > 0 else '#28a745'};">
                <h3>{int(total_anomalies)}</h3>
                <p>Anomalies Detected</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{anomaly_rate:.1f}%</h3>
                <p>Anomaly Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Final Analysis - Similar to Manual Prediction
        st.markdown("## 🎯 Final Session Analysis")
        
        # Get last prediction result for detailed analysis
        last_result = st.session_state.streaming_data[-1]
        
        # Display final prediction results (like Manual Prediction)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{last_result['predicted_kwh']:.2f} kWh</h3>
                <p>Last Predicted</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if last_result.get('actual_kwh'):
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{last_result['actual_kwh']:.2f} kWh</h3>
                    <p>Last Actual</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No actual data provided")
        
        with col3:
            if last_result.get('residual_kwh') is not None:
                color = "#dc3545" if last_result['is_anomaly'] else "#28a745"
                st.markdown(f"""
                <div class="metric-card" style="background: {color};">
                    <h3>{last_result['residual_kwh']:.2f} kWh</h3>
                    <p>Last Residual</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("N/A")
        
        with col4:
            if last_result.get('error_pct') is not None:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{last_result['error_pct']:.2f}%</h3>
                    <p>Last Error %</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("N/A")
        
        # Global anomaly analysis
        st.markdown("### 🔍 Overall Session Assessment")
        
        # Determine overall session status - Simple logic: < 50% = Normal, >= 50% = Critical
        if anomaly_rate < 50:
            st.success(f"✅ Energy consumption is within normal range. ({anomaly_rate:.1f}% anomaly rate)")
        else:
            st.error(f"🚨 CRITICAL ALERT! Energy consumption is significantly abnormal! ({anomaly_rate:.1f}% anomaly rate)")
        
        # Show if alert was triggered
        if st.session_state.alert_triggered:
            st.error("🚨 Multiple consecutive anomalies were detected during the session!")
        
        st.markdown("---")
        
        # Final charts
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### 📈 Complete Time Series")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['predicted_kwh'],
                name='Predicted',
                line=dict(color='#667eea', width=2)
            ))
            if avg_actual:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['actual_kwh'],
                    name='Actual',
                    line=dict(color='#28a745', width=2)
                ))
            fig.update_layout(
                title="Energy Consumption Over Time",
                xaxis_title="Data Point",
                yaxis_title="Energy (kWh)",
                height=400
            )
            st.plotly_chart(fig, width='stretch')
        
        with col_right:
            st.markdown("### 🎯 Anomaly Distribution")
            anomaly_counts = df['is_anomaly'].value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=['Normal', 'Anomaly'],
                values=[anomaly_counts.get(False, 0), anomaly_counts.get(True, 0)],
                marker_colors=['#28a745', '#dc3545'],
                hole=0.4
            )])
            fig.update_layout(
                title="Detection Distribution",
                height=400
            )
            st.plotly_chart(fig, width='stretch')
        
        # Detailed data table
        st.markdown("### 📋 Detailed Data")
        
        # Display data table with highlighting
        display_df = df[['predicted_kwh', 'actual_kwh', 'residual_kwh', 'error_pct', 'is_anomaly']].copy()
        display_df.columns = ['Predicted (kWh)', 'Actual (kWh)', 'Residual (kWh)', 'Error (%)', 'Anomaly']
        display_df['Anomaly'] = display_df['Anomaly'].apply(lambda x: '⚠️ Yes' if x else '✅ No')
        
        st.dataframe(
            display_df,
            width='stretch',
            height=300
        )
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Session Data (CSV)",
            data=csv,
            file_name=f"streaming_session_{st.session_state.vehicle_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width='stretch'
        )
        
        # Thresholds info
        if st.session_state.streaming_data:
            last_result = st.session_state.streaming_data[-1]
            if 'thresholds' in last_result:
                st.markdown("### 📏 Detection Thresholds Used")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Residual Threshold",
                        f"{last_result['thresholds']['residual_threshold_kwh_p95']:.2f} kWh",
                        help="95th percentile of residuals from baseline"
                    )
                
                with col2:
                    st.metric(
                        "Error Threshold",
                        f"{last_result['thresholds']['error_pct_threshold_p95']:.2f}%",
                        help="95th percentile of error percentage from baseline"
                    )
                
                # Show comparison chart like Manual Prediction
                st.markdown("### 📊 Threshold Comparison")
                fig = go.Figure()
                
                # Add residual threshold line
                fig.add_hline(
                    y=last_result['thresholds']['residual_threshold_kwh_p95'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Residual Threshold"
                )
                
                # Plot residuals
                residuals = [point.get('residual_kwh', 0) for point in st.session_state.streaming_data if point.get('residual_kwh') is not None]
                if residuals:
                    colors = ['red' if point['is_anomaly'] else 'green' for point in st.session_state.streaming_data if point.get('residual_kwh') is not None]
                    fig.add_trace(go.Bar(
                        y=residuals,
                        marker_color=colors,
                        name='Residuals',
                        showlegend=False
                    ))
                
                fig.update_layout(
                    title="Residuals vs Threshold",
                    xaxis_title="Data Point",
                    yaxis_title="Residual (kWh)",
                    height=400
                )
                st.plotly_chart(fig, width='stretch')
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset & New Session", width='stretch'):
            result = st.session_state.api_client.reset_stream(st.session_state.vehicle_id)
            if result:
                st.session_state.streaming_active = False
                st.session_state.streaming_data = []
                st.session_state.anomaly_count = 0
                st.session_state.alert_triggered = False
                st.session_state.stream_finished = False
                st.success("✅ Stream reset! Ready for new session.")
                time.sleep(1)
                st.rerun()
    
    with col2:
        if st.button("📈 View Dashboard", width='stretch'):
            st.switch_page("pages/4_📈_Dashboard.py")
    
    with col3:
        if st.button("🏠 Home", width='stretch'):
            st.switch_page("app.py")

# Sidebar
with st.sidebar:
    st.markdown("### 📡 Streaming Info")
    
    if st.session_state.streaming_active:
        st.success("🔴 STREAMING ACTIVE")
        st.markdown(f"**Mode**: {st.session_state.selected_mode.upper()}")
        st.markdown(f"**Vehicle**: {st.session_state.vehicle_id}")
    elif st.session_state.stream_finished:
        st.info("✅ Session Completed")
        st.markdown(f"**Total Points**: {len(st.session_state.streaming_data)}")
        st.markdown(f"**Anomalies**: {st.session_state.anomaly_count}")
    else:
        st.info("Configure and start streaming")
    
    st.markdown("---")
    st.warning("""
    **⚠️ Important:**
    Always reset the stream before starting a new scenario to clear previous state!
    """)
