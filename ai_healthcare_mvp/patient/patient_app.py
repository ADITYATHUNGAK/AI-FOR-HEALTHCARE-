import streamlit as st
import os
import sys
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv
from llama_cpp import Llama

# Imports for features
from streamlit_mic_recorder import speech_to_text
import pandas as pd
import plotly.express as px
from fpdf import FPDF

# --- ALLOW IMPORTS FROM ROOT ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from firebase_config.firebase_connection import connect_to_firestore
from utils.risk_calculator import ai_health_risk_score

# ================= FIREBASE =================
db = connect_to_firestore()
if not db:
    st.error("Firebase connection failed")
    st.stop()

# ================= LOCAL AI MODEL SETUP =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "Llama-3.2-3B-Instruct.Q4_K_M.gguf")

@st.cache_resource
def load_local_model():
    if not os.path.exists(MODEL_PATH):
        st.error(f"❌ Model file not found at: {MODEL_PATH}")
        return None
    return Llama(model_path=MODEL_PATH, n_ctx=2048, n_threads=4, verbose=False)

llm = load_local_model()

# ================= HELPER FUNCTIONS =================
def generate_pdf(patient_name, date, doctor, pain, steps, notes, ai_rec):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Official Medical Triage Report", ln=True, align='C')
    pdf.line(10, 20, 200, 20)
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(0, 8, f"Patient Name: {patient_name}", ln=True)
    pdf.cell(0, 8, f"Date: {date}", ln=True)
    pdf.cell(0, 8, f"Assigned To: {doctor}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Vitals & Symptoms:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"- Pain Level: {pain}/10", ln=True)
    pdf.cell(0, 8, f"- Steps Walked: {steps}", ln=True)
    clean_notes = str(notes).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, f"- Patient Notes: {clean_notes}")
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "AI Assessment:", ln=True)
    pdf.set_font("Arial", size=12)
    clean_ai_rec = str(ai_rec).encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, clean_ai_rec)
    return bytes(pdf.output())

def hash_password(password):
    """Encrypts passwords before saving to database"""
    return hashlib.sha256(password.encode()).hexdigest()

# ================= AUTHENTICATION LAYER =================
st.set_page_config(page_title="Patient Portal")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Patient Login Portal")
    st.write("Please authenticate to access your private medical records.")
    
    auth_mode = st.radio("Select Action:", ["Login", "Sign Up"], horizontal=True)
    
    with st.form("auth_form"):
        username = st.text_input("Full Name")
        password = st.text_input("Password", type="password")
        submit_auth = st.form_submit_button("Submit")
        
        if submit_auth:
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                hashed_pw = hash_password(password)
                user_ref = db.collection("users").document(username)
                doc = user_ref.get()
                
                if auth_mode == "Sign Up":
                    if doc.exists:
                        st.error("User already exists! Please log in.")
                    else:
                        user_ref.set({"password": hashed_pw})
                        st.success("Account created successfully! You are now logged in.")
                        st.session_state.logged_in = True
                        st.session_state.patient_name = username
                        st.rerun()
                        
                elif auth_mode == "Login":
                    if not doc.exists:
                        st.error("User not found. Please check your spelling or Sign Up.")
                    elif doc.to_dict().get("password") != hashed_pw:
                        st.error("Incorrect password.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.patient_name = username
                        st.rerun()
    
    # STOP EXECUTION HERE IF NOT LOGGED IN
    st.stop()


# ================= MAIN APP UI (ONLY VISIBLE IF LOGGED IN) =================
st.title("🧑‍⚕️ Patient Portal")
col1, col2 = st.columns([4, 1])
with col1:
    st.write(f"Welcome back, **{st.session_state.patient_name}**.")
with col2:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

st.divider()

# Create Tabs
tab_submit, tab_records, tab_chat = st.tabs(["📝 New Report", "📂 My Records", "💬 AI Chatbot"])
# Name is now securely locked to the logged-in session
name = st.session_state.patient_name 

# ================= TAB 1: SUBMIT REPORT =================
with tab_submit:
    st.subheader("Submit a Health Update")
    
    department = st.selectbox("Department", [
        "Orthopedics", "Cardiology", "Neurology", "General Medicine",
        "Dermatology", "ENT", "Gastroenterology", "Physiotherapy"
    ])

    doctor_map = {
        "Orthopedics": "Dr. Evelyn Reed", "Cardiology": "Dr. Marcus Chen",
        "Neurology": "Dr. Sarah Jones", "General Medicine": "Dr. Alex Thompson",
        "Dermatology": "Dr. Chloe Davis", "ENT": "Dr. Omar Khan",
        "Gastroenterology": "Dr. Lena Rodriguez", "Physiotherapy": "Dr. Ben Carter"
    }
    doctor = doctor_map[department]
    st.write("Assigned Doctor:", doctor)

    pain = st.slider("Pain Level", 0, 10, 5)
    steps = st.number_input("Steps", 0)
    medicine = st.selectbox("Medicine Taken?", ["Yes", "No"])
    sleep = st.number_input("Sleep Hours", 0.0, 24.0, 7.0)
    mood = st.selectbox("Mood", ["Neutral", "Happy", "Sad", "Tired", "Stressed"])
    
    st.write("🎙️ **Describe your symptoms:**")
    spoken_text = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT')
    default_notes = spoken_text if spoken_text else ""
    notes = st.text_area("Symptoms/Notes", value=default_notes, height=100)

    if st.button("Submit Report", type="primary"):
        level, score, rec = ai_health_risk_score(steps, pain, medicine, sleep, mood)
        db.collection("patients").add({
            "name": name,
            "assigned_doctor": doctor,
            "steps_walked": float(steps or 0),
            "pain_level": float(pain or 0),
            "medicine_taken": medicine,
            "sleep_hours": float(sleep or 0),
            "mood": mood,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "risk_level": level,
            "risk_score": score,
            "ai_recommendation": rec,
            "doctor_notes": "" 
        })
        st.success(f"Report submitted successfully! Sent to {doctor}.")

# ================= TAB 2: MY RECORDS & DOCTOR NOTES =================
with tab_records:
    st.subheader("Past Reports & Doctor Feedback")
    
    if st.button("🔄 Fetch My Records"):
        docs = db.collection("patients").where("name", "==", name).stream()
        records = [d.to_dict() for d in docs]
        
        if not records:
            st.info("No records found.")
        else:
            st.markdown("### 📉 Your Health Trajectory")
            df = pd.DataFrame(records)
            
            if 'timestamp' in df.columns and 'pain_level' in df.columns:
                df['Date'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values(by='Date')
                fig = px.line(df, x='Date', y='pain_level', markers=True, 
                              title="Pain Level Over Time", labels={'pain_level': 'Reported Pain (0-10)'})
                fig.update_traces(line_color='#FF4B4B')
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            st.markdown("### 📋 Detailed Report History")

            records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            for i, r in enumerate(records):
                with st.container(border=True):
                    raw_time = r.get("timestamp", "")
                    try:
                        dt = datetime.fromisoformat(raw_time)
                        display_time = dt.strftime("%B %d, %Y at %H:%M")
                    except:
                        display_time = "Unknown Date"
                        
                    st.markdown(f"### Report from {display_time}")
                    st.caption(f"Reviewed by {r.get('assigned_doctor', 'Unknown Doctor')}")
                    st.write(f"**Risk Level:** {r.get('risk_level', 'Unknown')} (Score: {r.get('risk_score', 0)})")
                    st.write(f"**AI Recommendation:** {r.get('ai_recommendation', 'None')}")
                    
                    doc_note = r.get("doctor_notes", "").strip()
                    if doc_note:
                        st.success(f"🩺 **Doctor's Note:** {doc_note}")
                    else:
                        st.info("🩺 *Doctor has not added notes to this report yet.*")
                        
                    with st.expander("View what you submitted"):
                        st.write(f"**Pain:** {r.get('pain_level', '-')} | **Steps:** {r.get('steps_walked', '-')} | **Medicine:** {r.get('medicine_taken', '-')}")
                        st.write(f"**Your Notes:** {r.get('notes', 'None')}")

                    pdf_bytes = generate_pdf(
                        patient_name=name, date=display_time, doctor=r.get('assigned_doctor', 'Unknown'),
                        pain=r.get('pain_level', 0), steps=r.get('steps_walked', 0),
                        notes=r.get('notes', 'None'), ai_rec=r.get('ai_recommendation', 'None')
                    )
                    
                    st.download_button(
                        label="📄 Download Report as PDF", data=pdf_bytes,
                        file_name=f"Medical_Report_{name.replace(' ', '_')}.pdf", mime="application/pdf",
                        key=f"pdf_btn_{i}_{r.get('timestamp', 'no_date')}"
                    )

# ================= TAB 3: CHATBOT (LOCAL AI WITH RAG MEMORY) =================
with tab_chat:
    if llm is None:
        st.warning("Chatbot is currently unavailable.")
    else:
        st.subheader("💬 Health Assistant Chatbot")

        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your completely private AI Health Assistant. I have access to your past medical records. How can I help you today?"}]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).markdown(msg["content"])

        prompt = st.chat_input("Ask something about your symptoms or history...")

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)

            # --- RAG MEMORY INJECTION ---
            # 1. Fetch the user's history silently from Firebase
            docs = db.collection("patients").where("name", "==", name).stream()
            records = [d.to_dict() for d in docs]
            records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            recent_records = records[:3] # Grab only the 3 most recent reports
            
            # 2. Build the history string
            history_context = "Patient's Recent Medical History (Do not mention this unless relevant):\n"
            if not recent_records:
                history_context += "No previous records found.\n"
            else:
                for r in recent_records:
                    raw_time = r.get("timestamp", "")[:10]
                    history_context += f"- Date: {raw_time} | Pain Level: {r.get('pain_level')}/10 | Notes: {r.get('notes')}\n"

            # 3. Inject the history directly into the AI's Brain (System Prompt)
            system_instruction = f"You are a safe medical assistant. Rules: No diagnosis. No prescriptions. Always recommend doctor consultation.\n\n{history_context}"
            chat_prompt = f"<|im_start|>system\n{system_instruction}<|im_end|>\n"
            
            # 4. Append the conversation history
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    chat_prompt += f"<|im_start|>user\n{msg['content']}<|im_end|>\n"
                elif msg["role"] == "assistant":
                    chat_prompt += f"<|im_start|>assistant\n{msg['content']}<|im_end|>\n"
            
            chat_prompt += "<|im_start|>assistant\n"

            # 5. Generate Response
            try:
                response = llm(
                    chat_prompt,
                    max_tokens=256,
                    stop=["<|im_end|>"], 
                    temperature=0.4
                )
                reply = response["choices"][0]["text"].strip()
            except Exception as e:
                reply = f"Error generating response: {e}"

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").markdown(reply)
