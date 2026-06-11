import streamlit as st
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- ALLOW IMPORTS FROM ROOT ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

# Import custom modules
from firebase_config.firebase_connection import connect_to_firestore
from utils.risk_calculator import ai_health_risk_score

# ================= FIREBASE =================
db = connect_to_firestore()

if not db:
    st.error("Firebase connection failed")
    st.stop()

# ================= GEMINI =================
# THE FIX: Cache the client so it stays open during page reloads
@st.cache_resource
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

client = get_gemini_client()

SYSTEM_PROMPT = """
You are a safe medical assistant.
Rules:
- No diagnosis
- No prescriptions
- Always recommend doctor consultation
"""

# ================= UI HEADER =================
st.set_page_config(page_title="Patient Portal")
st.title("🧑‍⚕️ Patient Portal")

st.info("Please enter your name below. We will use this to save your new reports and find your past records.")
name = st.text_input("Full Name (Your Identifier)", key="patient_name")

st.divider()

# Create Tabs for better organization
tab_submit, tab_records, tab_chat = st.tabs(["📝 New Report", "📂 My Records", "💬 AI Chatbot"])

# ================= TAB 1: SUBMIT REPORT =================
with tab_submit:
    st.subheader("Submit a Health Update")
    
    department = st.selectbox("Department", [
        "Orthopedics", "Cardiology", "Neurology", "General Medicine",
        "Dermatology", "ENT", "Gastroenterology", "Physiotherapy"
    ])

    doctor_map = {
        "Orthopedics": "Dr. Evelyn Reed",
        "Cardiology": "Dr. Marcus Chen",
        "Neurology": "Dr. Sarah Jones",
        "General Medicine": "Dr. Alex Thompson",
        "Dermatology": "Dr. Chloe Davis",
        "ENT": "Dr. Omar Khan",
        "Gastroenterology": "Dr. Lena Rodriguez",
        "Physiotherapy": "Dr. Ben Carter"
    }

    doctor = doctor_map[department]
    st.write("Assigned Doctor:", doctor)

    pain = st.slider("Pain Level", 0, 10, 5)
    steps = st.number_input("Steps", 0)
    medicine = st.selectbox("Medicine Taken?", ["Yes", "No"])
    sleep = st.number_input("Sleep Hours", 0.0, 24.0, 7.0)
    mood = st.selectbox("Mood", ["Neutral", "Happy", "Sad", "Tired", "Stressed"])
    notes = st.text_area("Symptoms/Notes")

    if st.button("Submit Report", type="primary"):
        if not name:
            st.warning("Please enter your name at the top of the page.")
        else:
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
                
                # FLAT STRUCTURE
                "risk_level": level,
                "risk_score": score,
                "ai_recommendation": rec,
                "doctor_notes": "" # Initialize empty string for doctor notes
            })

            st.success(f"Report submitted successfully! Sent to {doctor}.")


# ================= TAB 2: MY RECORDS & DOCTOR NOTES =================
with tab_records:
    st.subheader("Past Reports & Doctor Feedback")
    
    if st.button("🔄 Fetch My Records"):
        if not name:
            st.warning("Please enter your name at the top of the page to find your records.")
        else:
            # Query Firebase for this exact patient name
            docs = db.collection("patients").where("name", "==", name).stream()
            records = [d.to_dict() for d in docs]
            
            if not records:
                st.info(f"No records found for '{name}'.")
            else:
                # Sort records by timestamp (newest first)
                records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                
                for r in records:
                    with st.container(border=True):
                        # Format the date nicely
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
                        
                        # Display the Doctor's Note prominently
                        doc_note = r.get("doctor_notes", "").strip()
                        if doc_note:
                            st.success(f"🩺 **Doctor's Note:** {doc_note}")
                        else:
                            st.info("🩺 *Doctor has not added notes to this report yet.*")
                            
                        with st.expander("View what you submitted"):
                            st.write(f"**Pain:** {r.get('pain_level', '-')} | **Steps:** {r.get('steps_walked', '-')} | **Medicine:** {r.get('medicine_taken', '-')}")
                            st.write(f"**Your Notes:** {r.get('notes', 'None')}")


# ================= TAB 3: CHATBOT =================
with tab_chat:
    if not client:
        st.warning("Chatbot is currently unavailable (API Key missing).")
    else:
        st.subheader("💬 Health Assistant Chatbot")

        if "chat_session" not in st.session_state:
            st.session_state.chat_session = client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.3 
                )
            )

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I am your AI Health Assistant. How can I help you today?"}
            ]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).markdown(msg["content"])

        prompt = st.chat_input("Ask something about your symptoms...")

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)

            try:
                # Send the message directly using the session state chat
                response = st.session_state.chat_session.send_message(prompt)
                reply = response.text
            except Exception as e:
                reply = f"Error: {e}"

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").markdown(reply)