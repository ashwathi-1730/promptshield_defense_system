# evolution/dashboard.py
import streamlit as st
import json
import pandas as pd
import os
import sqlite3

st.set_page_config(layout="wide", page_title="PromptShield Dashboard")

st.title("🛡️ PromptShield: Defense Operations")

# --- TAB 1: ATTACK LOGS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Recent Attack Logs")
    if os.path.exists("data/logs.db"):
        conn = sqlite3.connect("data/logs.db")
        df = pd.read_sql_query("SELECT * FROM flagged_prompts ORDER BY timestamp DESC", conn)
        st.dataframe(df, height=300)
        conn.close()
    else:
        st.info("No logs found yet.")

# --- TAB 2: PENDING RULES ---
with col2:
    st.subheader("AI Suggested Rules (Pending)")
    
    # Load Pending
    pending_rules = []
    if os.path.exists("data/pending_rules.json"):
        with open("data/pending_rules.json", "r") as f:
            try: pending_rules = json.load(f)
            except: pass
            
    if not pending_rules:
        st.success("No pending rules.")
    else:
        for i, rule in enumerate(pending_rules):
            with st.expander(f"Rule: {rule['pattern']}"):
                st.write(f"**Reason:** {rule['reason']}")
                c1, c2 = st.columns(2)
                
                # APPROVE BUTTON
                if c1.button("Approve", key=f"app_{i}"):
                    # Add to Active Rules
                    with open("data/rules.json", "r+") as f:
                        data = json.load(f)
                        if rule['pattern'] not in data['patterns']:
                            data['patterns'].append(rule['pattern'])
                            f.seek(0)
                            json.dump(data, f, indent=4)
                            f.truncate()
                    
                    # Remove from Pending
                    pending_rules.pop(i)
                    with open("data/pending_rules.json", "w") as f:
                        json.dump(pending_rules, f, indent=4)
                    st.rerun()
                
                # REJECT BUTTON
                if c2.button("Reject", key=f"rej_{i}"):
                    pending_rules.pop(i)
                    with open("data/pending_rules.json", "w") as f:
                        json.dump(pending_rules, f, indent=4)
                    st.rerun()

# --- TAB 3: ACTIVE CONFIGURATION ---
st.subheader("Active Knowledge Base (rules.json)")
if os.path.exists("data/rules.json"):
    with open("data/rules.json", "r") as f:
        st.json(json.load(f))