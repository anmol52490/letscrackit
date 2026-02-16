import streamlit as st
import pandas as pd
import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

# Import our custom modules
from src.chatbot import get_gemini_response
from src.agents import judge, attack
from src.guardrails import ml_engine, filter_utils

# --- CONFIG & SETUP ---
load_dotenv()
st.set_page_config(page_title="F5 Style AI Guardrail Demo", layout="wide")

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "data" / "red_team_logs.csv"

# Ensure data directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Initialize Session State for Logs
if "logs" not in st.session_state:
    if os.path.exists(LOG_FILE):
        try:
            st.session_state.logs = pd.read_csv(LOG_FILE)
        except pd.errors.EmptyDataError:
            st.session_state.logs = pd.DataFrame(columns=["Time", "Type", "Prompt", "Guardrail", "Action"])
    else:
        st.session_state.logs = pd.DataFrame(columns=["Time", "Type", "Prompt", "Guardrail", "Action"])


# Load Resources
banned_phrases = filter_utils.load_attack_db()
ml_guard = ml_engine.SimpleGuardrailML()

# --- SIDEBAR ---
with st.sidebar:
    st.image("assets/logo.png", width=150) # Make sure you have a logo.png
    st.title("Control Panel")
    st.markdown("---")
    
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        
    st.markdown("### 🔴 Red Team Lab")
    if st.button("🚀 Launch Attack Simulation"):
        # Generate Attack
        attack_type, tricky_prompt = attack.generate_attack()
        st.session_state.last_attack_prompt = tricky_prompt
        st.session_state.last_attack_type = attack_type
        st.success(f"Generated: {attack_type}")

# --- MAIN UI ---
st.title("🛡️ AI Guardrail & Red Team Demo")
st.markdown("Compare how different security layers handle user prompts.")

# Input Area
user_input = st.text_input("Enter your prompt:", value=st.session_state.get("last_attack_prompt", ""))

if st.button("Submit Prompt") and user_input:
    
    # Create 3 Columns for Comparison
    col1, col2, col3 = st.columns(3)
    
    # --- COLUMN 1: NO GUARDRAIL ---
    with col1:
        st.subheader("1. No Protection")
        st.caption("Raw LLM Interaction")
        with st.spinner("Asking Gemini..."):
            raw_response = get_gemini_response(user_input)
            st.error(raw_response) # Using error color to indicate 'Dangerous' if unchecked

    # --- COLUMN 2: LLM JUDGE (Agent) ---
    with col2:
        st.subheader("2. AI Agent Judge")
        st.caption("LLM checking another LLM")
        with st.spinner("Judge is thinking..."):
            is_safe, reason = judge.evaluate_prompt(user_input)
            
            if is_safe:
                st.success("✅ PASSED")
                response = get_gemini_response(user_input)
                st.write(response)
                action = "Passed"
            else:
                st.warning("⛔ BLOCKED")
                st.write(f"Reason: {reason}")
                action = "Blocked"
                
    # --- COLUMN 3: HYBRID GUARDRAIL (F5 Style) ---
    with col3:
        st.subheader("3. ML + Static Guard")
        st.caption("Fast Machine Learning Check")
        
        # Check 1: Exact Match
        is_exact_blocked, exact_reason = filter_utils.check_exact_match(user_input, banned_phrases)
        
        # Check 2: ML Model
        is_ml_blocked, ml_conf = ml_guard.predict(user_input)
        
        if is_exact_blocked:
            st.error("⛔ BLOCKED (Database Match)")
            st.write(exact_reason)
            final_action = "Blocked (Static)"
        elif is_ml_blocked:
            st.error(f"⛔ BLOCKED (ML Model)")
            st.write(f"Confidence: {ml_conf:.2%}")
            final_action = "Blocked (ML)"
        else:
            st.success("✅ PASSED")
            response = get_gemini_response(user_input)
            st.write(response)
            final_action = "Passed"

    
    # --- LOGGING ---
    new_log = {
        "Time": datetime.datetime.now().strftime("%H:%M:%S"),
        "Type": st.session_state.get("last_attack_type", "Manual User"),
        "Prompt": user_input,
        "Guardrail": "Hybrid ML",
        "Action": final_action
    }
    
    # Convert to DataFrame
    new_log_df = pd.DataFrame([new_log])

    # 1. Update Session State (for UI display)
    st.session_state.logs = pd.concat([st.session_state.logs, new_log_df], ignore_index=True)
    
    # 2. Save to CSV (Persistent Storage)
    new_log_df.to_csv(LOG_FILE, mode='a', header=not LOG_FILE.exists(), index=False)

# --- LOGS DISPLAY ---
st.markdown("---")
st.subheader("📊 Security Logs (Red Team Results)")
st.dataframe(st.session_state.logs, width=True)