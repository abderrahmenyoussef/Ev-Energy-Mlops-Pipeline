"""
Database utilities for user authentication
"""
import mysql.connector
from mysql.connector import Error
import hashlib
import streamlit as st
from config import DB_CONFIG


def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"Database connection error: {e}")
        return None


def init_database():
    """Initialize database tables if they don't exist"""
    connection = get_db_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Create users table
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            full_name VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL
        )
        """
        cursor.execute(create_users_table)
        
        # Create user sessions table
        create_sessions_table = """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            vehicle_id VARCHAR(50),
            session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_end TIMESTAMP NULL,
            predictions_count INT DEFAULT 0,
            anomalies_count INT DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
        cursor.execute(create_sessions_table)
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        st.error(f"Database initialization error: {e}")
        return False


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, email: str, password: str, full_name: str = "") -> bool:
    """Create a new user"""
    connection = get_db_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        password_hash = hash_password(password)
        
        query = """
        INSERT INTO users (username, email, password_hash, full_name)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (username, email, password_hash, full_name))
        connection.commit()
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        if "Duplicate entry" in str(e):
            st.error("Username or email already exists")
        else:
            st.error(f"Error creating user: {e}")
        return False


def verify_user(username: str, password: str) -> dict:
    """Verify user credentials and return user data"""
    connection = get_db_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        password_hash = hash_password(password)
        
        query = """
        SELECT id, username, email, full_name
        FROM users
        WHERE username = %s AND password_hash = %s
        """
        cursor.execute(query, (username, password_hash))
        user = cursor.fetchone()
        
        if user:
            # Update last login
            update_query = "UPDATE users SET last_login = NOW() WHERE id = %s"
            cursor.execute(update_query, (user['id'],))
            connection.commit()
        
        cursor.close()
        connection.close()
        return user
        
    except Error as e:
        st.error(f"Authentication error: {e}")
        return None


def log_session(user_id: int, vehicle_id: str, predictions: int, anomalies: int):
    """Log user session data"""
    connection = get_db_connection()
    if connection is None:
        return
    
    try:
        cursor = connection.cursor()
        
        query = """
        INSERT INTO user_sessions (user_id, vehicle_id, predictions_count, anomalies_count, session_end)
        VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(query, (user_id, vehicle_id, predictions, anomalies))
        connection.commit()
        
        cursor.close()
        connection.close()
        
    except Error as e:
        st.error(f"Session logging error: {e}")
