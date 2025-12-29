"""
Main Streamlit App - Home/Login Page
"""
import streamlit as st
from utils.auth import check_authentication, login_user, logout_user, signup_user
from utils.database import init_database
from utils.api_client import EVEnergyAPIClient
from config import APP_TITLE, APP_ICON

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .feature-card {
        padding: 1.5rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .login-box {
        padding: 2rem;
        border-radius: 15px;
        background: white;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    .success-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        font-size: 1rem;
        font-weight: bold;
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
if "db_initialized" not in st.session_state:
    if init_database():
        st.session_state.db_initialized = True

# Initialize API client
if "api_client" not in st.session_state:
    st.session_state.api_client = EVEnergyAPIClient()


def show_home():
    """Show home page for authenticated users"""
    st.markdown(f'<h1 class="main-header">{APP_ICON} {APP_TITLE}</h1>', unsafe_allow_html=True)
    
    # Welcome message
    user = st.session_state.user
    st.markdown(f"### Welcome back, **{user['full_name'] or user['username']}**! 👋")
    
    # API Status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        health = st.session_state.api_client.health_check()
        if health.get("status") == "ok":
            st.success("✅ API Connected")
            st.metric("Model Status", "Loaded" if health.get("model_loaded") else "Not Loaded")
        else:
            st.error("❌ API Disconnected")
    
    with col2:
        st.info("📊 **User Stats**")
        st.metric("Sessions", st.session_state.get("total_sessions", 0))
        st.metric("Predictions", st.session_state.get("total_predictions", 0))
    
    with col3:
        st.warning("⚠️ **Anomalies Detected**")
        st.metric("Total Anomalies", st.session_state.get("total_anomalies", 0))
    
    st.markdown("---")
    
    # Features
    st.markdown("### 🚀 Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Manual Prediction</h3>
            <p>Enter vehicle parameters manually and get instant energy consumption predictions with anomaly detection.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📡 Real-Time Streaming</h3>
            <p>Connect to your electric vehicle and monitor energy consumption in real-time with live visualizations.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📈 Dashboard</h3>
            <p>View comprehensive analytics, drift detection, and historical data with interactive charts.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔮 Make Prediction", width='stretch'):
            st.switch_page("pages/2_📊_Manual_Prediction.py")
    
    with col2:
        if st.button("📡 Start Streaming", width='stretch'):
            st.switch_page("pages/3_📡_Real_Time_Streaming.py")
    
    with col3:
        if st.button("📈 View Dashboard", width='stretch'):
            st.switch_page("pages/4_📈_Dashboard.py")
    
    with col4:
        if st.button("🚪 Logout", width='stretch'):
            logout_user()
            st.rerun()


def show_login():
    """Show login/signup page"""
    st.markdown(f'<h1 class="main-header">{APP_ICON} {APP_TITLE}</h1>', unsafe_allow_html=True)
    
    st.markdown("### Real-Time Energy Monitoring for Electric Vehicles")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        st.markdown("### Sign In to Your Account")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submitted = st.form_submit_button("Login", width='stretch')
            
            if submitted:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    with st.spinner("Authenticating..."):
                        if login_user(username, password):
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid username or password")
    
    with tab2:
        st.markdown("### Create a New Account")
        
        with st.form("signup_form"):
            new_username = st.text_input("Username", placeholder="Choose a username", key="signup_username")
            new_email = st.text_input("Email", placeholder="your.email@example.com", key="signup_email")
            new_full_name = st.text_input("Full Name", placeholder="Your full name", key="signup_fullname")
            new_password = st.text_input("Password", type="password", placeholder="Choose a strong password", key="signup_password")
            new_password_confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="signup_password_confirm")
            
            submitted = st.form_submit_button("Sign Up", width='stretch')
            
            if submitted:
                if not all([new_username, new_email, new_password, new_password_confirm]):
                    st.error("Please fill in all required fields")
                elif new_password != new_password_confirm:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    with st.spinner("Creating account..."):
                        if signup_user(new_username, new_email, new_password, new_full_name):
                            st.success("✅ Account created successfully! Please login.")
                            st.balloons()
                        else:
                            st.error("❌ Failed to create account. Username or email may already exist.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Powered by <strong>EV Energy MLOps Pipeline</strong></p>
        <p>🔒 Secure • 🚀 Fast • 📊 Accurate</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main app logic"""
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"## {APP_ICON} EV Energy Monitor")
        
        if check_authentication():
            user = st.session_state.user
            st.markdown(f"**Logged in as:** {user['username']}")
            st.markdown("---")
            
            if st.button("🚪 Logout", width='stretch'):
                logout_user()
                st.rerun()
        else:
            st.info("Please login to continue")
    
    # Main content
    if check_authentication():
        show_home()
    else:
        show_login()


if __name__ == "__main__":
    main()
