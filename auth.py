import streamlit as st
from mysql.connector import Error
import hashlib
import secrets

class Auth:
    def __init__(self, database):
        self.db = database
        self.setup_database()
    
    def setup_database(self):
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        cursor = self.db.connection.cursor()
        cursor.execute(create_users_table)
        self.db.connection.commit()
        cursor.close()

    def hash_password(self, password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, email, role='user'):
        try:
            cursor = self.db.connection.cursor()
            query = """
            INSERT INTO users (username, password_hash, email, role)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (username, self.hash_password(password), email, role))
            self.db.connection.commit()
            return True
        except Error as e:
            print(f"Error creating user: {e}")
            return False
        finally:
            cursor.close()
    
    def verify_user(self, username, password):
        try:
            cursor = self.db.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s AND password_hash = %s AND is_active = TRUE"
            cursor.execute(query, (username, self.hash_password(password)))
            user = cursor.fetchone()
            return user
        except Error as e:
            print(f"Error verifying user: {e}")
            return None
        finally:
            cursor.close()

def login_page():
    st.title("Login")
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        with st.container():
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            col = st.columns(1)[0]
            with col:
                if st.button("Login", use_container_width=True):
                    auth = Auth(st.session_state.db)
                    user = auth.verify_user(username, password)
                    
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.success("Successfully logged in!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            if st.button("Register", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
        
        return False
    
    return True

def register_page():
    st.title("Register")
    
    with st.container():
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        reg_email = st.text_input("Email", key="reg_email")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Create Account", use_container_width=True):
                if reg_password != reg_confirm_password:
                    st.error("Passwords do not match")
                    return
                
                auth = Auth(st.session_state.db)
                if auth.create_user(reg_username, reg_password, reg_email):
                    st.success("Registration successful! Please login.")
                    st.session_state.show_register = False
                    st.rerun()
                else:
                    st.error("Registration failed. Username or email might already exist.")
        
        with col2:
            if st.button("Back to Login", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()

def initialize_auth():
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
        
    if st.session_state.show_register:
        return register_page()
    else:
        return login_page()