"""
Authentication utilities
"""
import streamlit as st
from utils.database import verify_user, create_user, init_database


def check_authentication():
    """Check if user is authenticated"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user" not in st.session_state:
        st.session_state.user = None
    
    return st.session_state.authenticated


def login_user(username: str, password: str) -> bool:
    """Login user"""
    user = verify_user(username, password)
    
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        return True
    
    return False


def logout_user():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    
    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def signup_user(username: str, email: str, password: str, full_name: str = "") -> bool:
    """Sign up new user"""
    return create_user(username, email, password, full_name)


def require_authentication():
    """Decorator to require authentication for pages"""
    if not check_authentication():
        st.warning("Please login to access this page")
        st.stop()
