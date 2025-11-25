import streamlit as st
import requests
import pandas as pd
import sqlite3
import json
import os

# --- CONFIGURATION ---
API_URL = "http://localhost:8000/generate"
DB_PATH = "data/logs.db"
RULES_PATH = "data/rules.json"
PENDING_PATH = "data/pending_rules.json"

st.set_page_config(page_title="PromptShield", page_icon="🛡️", layout="wide")

# --- AUTHENTICATION & STATE ---
if "role" not in st.session_state:
    st.session_state.role = None

if "messages" not in st.session_state:
    st.session_state.messages = []

def login():
    st.markdown("## 🛡️ PromptShield Gateway")
    role_selection = st.radio("Select Access Level:", ["Standard User", "Security Engineer (Admin)"])
    
    if role_selection == "Security Engineer (Admin)":
        password = st.text_input("Enter Admin Password:", type="password")
        if st.button("Login"):
            if password == "admin123": # Simple hardcoded password for demo
                st.session_state.role = "Admin"
                st.rerun()
            else:
                st.error("Invalid Password")
    else:
        if st.button("Enter Chat"):
            st.session_state.role = "User"
            st.rerun()

def logout():
    st.session_state.role = None
    st.session_state.messages = []
    st.rerun()

# --- CHATBOT INTERFACE (For Users & Admins) ---
def render_chatbot():
    st.subheader("💬 Secure LLM Chat Interface")
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input Area
    if prompt := st.chat_input("Type your prompt here..."):
        # 1. Add User Message to UI
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Call the Backend API (Your Defense Engine)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing prompt for security threats..."):
                try:
                    response = requests.post(API_URL, json={"prompt": prompt})
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data["status"] == "blocked":
                            # Show Blocked Message
                            error_msg = f"🚫 **BLOCKED by {data['layer']}**\n\nReason: *{data['message']}*"
                            st.markdown(error_msg, unsafe_allow_html=True)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        else:
                            # Show Success Message
                            st.markdown(data["response"])
                            st.session_state.messages.append({"role": "assistant", "content": data["response"]})
                    else:
                        st.error("Error connecting to Defense Engine.")
                except Exception as e:
                    st.error(f"Connection Failed. Is uvicorn running? ({e})")

# --- ADMIN METRICS (Only for Admins) ---
# This reads the SAME data as Person B's code, but displays it here.
def render_admin_panel():
    st.divider()
    st.header("🛠️ Engineer Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Live Attack Logs")
        if os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                df = pd.read_sql_query("SELECT * FROM flagged_prompts ORDER BY timestamp DESC LIMIT 50", conn)
                conn.close()
                st.dataframe(df, height=300)
                st.metric("Total Attacks Intercepted", len(df))
            except Exception as e:
                st.error(f"Database Error: {e}")
        else:
            st.warning("No logs found yet.")

    with col2:
        st.subheader("📜 Active Rules")
        if os.path.exists(RULES_PATH):
            with open(RULES_PATH, "r") as f:
                rules = json.load(f)
            st.json(rules)
        else:
            st.warning("Rules file not found.")

# --- MAIN CONTROLLER ---
if st.session_state.role is None:
    login()

elif st.session_state.role == "User":
    # USER VIEW: Chatbot Only
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.markdown("### Status: 🟢 Online")
    st.sidebar.info("You are in User Mode. Security metrics are hidden.")
    render_chatbot()

elif st.session_state.role == "Admin":
    # ADMIN VIEW: Chatbot + Metrics
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.markdown("### Status: 🔴 ADMIN")
    
    tab1, tab2 = st.tabs(["Testing Interface (Chatbot)", "Security Metrics"])
    
    with tab1:
        render_chatbot()
    with tab2:
        render_admin_panel()