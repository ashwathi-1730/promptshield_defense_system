import streamlit as st
import json
import pandas as pd
import os
import sqlite3
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PromptShield Admin Console")

# --- AUTHENTICATION LOGIC ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_login():
    username = st.session_state["username"]
    password = st.session_state["password"]
    
    # HARDCODED CREDENTIALS (Change as needed)
    if username == "admin" and password == "secure123":
        st.session_state.authenticated = True
        del st.session_state["password"] # Clean up memory
        del st.session_state["username"]
    else:
        st.error("Invalid credentials")

if not st.session_state.authenticated:
    st.title("🛡️ PromptShield Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Login", on_click=check_login)
    st.stop() # Stop execution here if not logged in

# =========================================================
# MAIN DASHBOARD (Only visible after login)
# =========================================================

st.title("PromptShield Defense System | Admin Console")
st.markdown("---")

# --- SIDEBAR: LOGOUT ---
with st.sidebar:
    st.write(f"Logged in as: **Admin**")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

# --- SECTION 1: SYSTEM TELEMETRY ---
st.subheader("System Telemetry")

if os.path.exists("data/logs.db"):
    try:
        conn = sqlite3.connect("data/logs.db")
        df = pd.read_sql("SELECT * FROM flagged_prompts", conn)
        conn.close()
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Requests Blocked", len(df))
        col2.metric("Static Rule Hits", len(df[df['blocked_layer'] == 'Static Rule Checker']))
        col3.metric("ML Model Hits", len(df[df['blocked_layer'] == 'ML Classifier']))
        col4.metric("Output Violations", len(df[df['blocked_layer'] == 'Output Validator']))
        
        # Recent Logs Table
        st.write("Recent Security Events")
        st.dataframe(
            df.sort_values(by="timestamp", ascending=False).head(5),
            use_container_width=True,
            hide_index=True
        )
    except Exception as e:
        st.error(f"Error reading telemetry: {e}")
else:
    st.info("System initializing. No telemetry data available yet.")

st.markdown("---")

# --- SECTION 2: RULE GOVERNANCE ---
st.subheader("Autonomous Rule Governance")

c1, c2 = st.columns([2, 1])

# --- HELPER FUNCTIONS FOR FILE I/O ---
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            try: return json.load(f)
            except: return []
    return []

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

# --- PENDING RULES (Left Column) ---
with c1:
    st.write("##### Pending Rules (Requires Approval)")
    
    pending_rules = load_json("data/pending_rules.json")
    
    # Deduplicate pending rules for display (Optional visual cleanup)
    # We display them exactly as stored to ensure index matching
    
    if not pending_rules:
        st.success("No pending rules. All systems nominal.")
    else:
        # Iterate backwards to allow popping without breaking index
        # Or simply handle one action per rerun
        for i, rule in enumerate(pending_rules):
            with st.container(border=True):
                col_info, col_act = st.columns([3, 1])
                with col_info:
                    st.code(rule['pattern'], language="regex")
                    st.caption(f"Reasoning: {rule['reason']}")
                    st.caption(f"Source: {rule.get('source', 'Unknown')}")
                
                with col_act:
                    # APPROVE
                    if st.button("Approve", key=f"approve_{i}"):
                        # 1. Load Active Rules
                        active_data = load_json("data/rules.json")
                        if not isinstance(active_data, dict): # Handle init structure
                            active_data = {"patterns": [], "version": "1.0"}
                            
                        # 2. Add if not exists
                        if rule['pattern'] not in active_data.get('patterns', []):
                            active_data['patterns'].append(rule['pattern'])
                            save_json("data/rules.json", active_data)
                            
                        # 3. Remove from Pending
                        pending_rules.pop(i)
                        save_json("data/pending_rules.json", pending_rules)
                        
                        # 4. Rerun immediately
                        st.rerun()
                    
                    # REJECT
                    if st.button("Reject", key=f"reject_{i}"):
                        pending_rules.pop(i)
                        save_json("data/pending_rules.json", pending_rules)
                        st.rerun()

# --- ACTIVE RULES (Right Column) ---
with c2:
    st.write("##### Active Configuration")
    active_data = load_json("data/rules.json")
    if isinstance(active_data, dict):
        patterns = active_data.get('patterns', [])
        st.dataframe(
            pd.DataFrame(patterns, columns=["Active Patterns"]),
            use_container_width=True,
            hide_index=True
        )