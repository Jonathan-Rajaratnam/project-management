import streamlit as st
import os
from themes import THEMES

# theme_manager.py
def apply_theme(theme_name):
    theme = THEMES[theme_name]
    
    css = f"""
        <style>
            /* Main app */
            .stApp {{
                background-color: {theme["backgroundColor"]};
                color: {theme["textColor"]};
            }}
            
            /* Sidebar */
            .stSidebar {{
                background-color: {theme["secondaryBackgroundColor"]};
            }}
            
            /* Buttons */
            .stButton > button {{
                background-color: {theme["primaryColor"]} !important;
                color: white;
            }}
            
            /* Input fields */
            .stTextInput > div > div > input {{
                background-color: {theme["secondaryBackgroundColor"]};
                color: {theme["textColor"]};
            }}
            
            /* Select boxes */
            .stSelectbox > div > div > select {{
                background-color: {theme["secondaryBackgroundColor"]};
                color: {theme["textColor"]};
            }}
            
            /* Cards and containers */
            .stCard {{
                background-color: {theme["secondaryBackgroundColor"]};
                color: {theme["textColor"]};
            }}
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {{
                color: {theme["textColor"]};
            }}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def add_theme_selector():
    # Initialize theme in session state if not present
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = "Light"  # default theme
    
    with st.sidebar:
        selected_theme = st.selectbox(
            "Choose Theme",
            options=list(THEMES.keys()),
            key="theme_selector",
            index=list(THEMES.keys()).index(st.session_state.current_theme)
        )
        
        if selected_theme != st.session_state.current_theme:
            st.session_state.current_theme = selected_theme
            apply_theme(selected_theme)
            update_theme(selected_theme)
            st.rerun()

def update_theme(theme_name):
    config_path = ".streamlit/config.toml"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    theme = THEMES[theme_name]
    with open(config_path, "w") as f:
        f.write("[theme]\n")
        for key, value in theme.items():
            if isinstance(value, str):
                f.write(f'{key} = "{value}"\n')
            else:
                f.write(f'{key} = {value}\n')
    
    # Add debug print
    st.write(f"Theme updated to: {theme_name}")
    with open(config_path, 'r') as f:
        st.write("Config file contents:", f.read())