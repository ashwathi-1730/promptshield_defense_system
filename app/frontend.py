import streamlit as st
import requests

# --- CONFIGURATION ---
API_URL = "http://localhost:8000/generate"

st.set_page_config(page_title="PromptShield Chat", page_icon="🛡️", layout="wide")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CHATBOT INTERFACE ---
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
            with st.spinner("🛡️ Analyzing prompt for security threats..."):
                try:
                    response = requests.post(API_URL, json={"prompt": prompt})
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data["status"] == "blocked":
                            # Show Blocked Message with detailed info
                            error_msg = f"""
                            🚫 **Security Alert: Prompt Blocked**
                            
                            **Layer:** {data['layer']}  
                            **Reason:** {data['message']}  
                            **Details:** {data.get('details', 'N/A')}
                            
                            ---
                            *Your prompt was flagged as potentially malicious and has been blocked for security reasons. Please rephrase your request.*
                            """
                            st.error(data['message'])
                            st.markdown(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        else:
                            # Show AI Response (Safe)
                            ai_response = data["response"]
                            st.markdown(ai_response)
                            st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    else:
                        error_text = "⚠️ Error connecting to Defense Engine."
                        st.error(error_text)
                        st.session_state.messages.append({"role": "assistant", "content": error_text})
                except Exception as e:
                    error_text = f"❌ Connection Failed. Make sure the API server is running.\n\nError: {str(e)}"
                    st.error(error_text)
                    st.session_state.messages.append({"role": "assistant", "content": error_text})

# --- MAIN CONTROLLER ---
# Render the chatbot directly
st.title("🛡️ PromptShield - Secure LLM Chat")
st.markdown("### Protected by Multi-Layer AI Security")
render_chatbot()

# Sidebar info
st.sidebar.markdown("### 🛡️ PromptShield")
st.sidebar.markdown("**Status:** 🟢 Online")
st.sidebar.info("All prompts are automatically scanned for:\n- Injection attacks\n- Malicious patterns\n- Data leakage attempts")
st.sidebar.markdown("---")
st.sidebar.markdown("Built with ❤️ for safer AI")