import streamlit as st
import pandas as pd
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# --- ALLOW IMPORTS FROM ROOT ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from firebase_config.firebase_connection import connect_to_firestore

# ================= FIREBASE =================
db = connect_to_firestore()

if not db:
    st.error("❌ Firebase connection failed")
    st.stop()

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Doctor Dashboard", layout="wide")
st.title("🩺 Doctor Dashboard")

# ================= FETCH FUNCTIONS =================
@st.cache_data(ttl=60) # Cache to save database reads
def fetch_doctors():
    docs = db.collection("doctors").stream()
    return {d.to_dict().get("name"): d.to_dict().get("password", "1234") for d in docs}

def fetch_patients():
    docs = db.collection("patients").stream()
    out = []
    for d in docs:
        data = d.to_dict()
        data["_doc_id"] = d.id
        # THE FIX: Add utc=True to align all timezones and prevent sorting crashes
        data["timestamp_parsed"] = pd.to_datetime(data.get("timestamp"), errors="coerce", utc=True)
        out.append(data)
    return out

# ================= LOGIN =================
doctors = fetch_doctors()
doctor_names = ["Select Doctor"] + list(doctors.keys())

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("Doctor Login")
    selected = st.selectbox("Select Doctor:", doctor_names)

    if selected != "Select Doctor":
        password = st.text_input("Password:", type="password")

        if st.button("Login"):
            if password == doctors.get(selected):
                st.session_state.logged_in = True
                st.session_state.doctor_name = selected
                st.rerun()
            else:
                st.error("❌ Wrong password")
    st.stop()

# ================= DASHBOARD HEADER =================
current_doctor = st.session_state.doctor_name

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"Welcome, {current_doctor}")
with col2:
    if st.button("🔄 Refresh Patient Data", use_container_width=True):
        st.rerun()

# ================= PATIENT DATA =================
patients = fetch_patients()
df = pd.DataFrame(patients)

if df.empty or "assigned_doctor" not in df.columns:
    st.info("No patients found in the database.")
    st.stop()

# Filter patients for the logged-in doctor
df["assigned_doctor"] = df["assigned_doctor"].fillna("Unassigned")
df = df[df["assigned_doctor"] == current_doctor]

if df.empty:
    st.info("You have no patients assigned to you currently.")
    st.stop()

# ================= DATA CLEANUP & SORTING =================
# 1. Force risk_score to be numeric
if "risk_score" not in df.columns:
    df["risk_score"] = 0
df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(0)

# 2. Handle completely missing timestamps to prevent NaT sorting errors
# We fill missing times with the oldest possible date so they sink to the bottom
fallback_time = pd.Timestamp.min.tz_localize("UTC")
df["timestamp_parsed"] = df["timestamp_parsed"].fillna(fallback_time)

# 3. Safe Sorting
df = df.sort_values(
    by=["risk_score", "timestamp_parsed"],
    ascending=[False, False]
)

# ================= UI DISPLAY =================
st.divider()

for _, row in df.iterrows():
    risk_level = row.get("risk_level", "Unknown")
    if risk_level == "High":
        status_color = "🔴"
    elif risk_level == "Moderate":
        status_color = "🟠"
    else:
        status_color = "🟢"

    with st.container(border=True):
        col_info, col_risk = st.columns([2, 1])
        
        with col_info:
            st.markdown(f"### 👤 {row.get('name', 'Unknown')}")
            st.write(
                f"**Pain:** {row.get('pain_level', '-')} / 10 | "
                f"**Steps:** {row.get('steps_walked', '-')} | "
                f"**Medicine Taken:** {row.get('medicine_taken', '-')}"
            )
            
            # Format the timestamp nicely for the UI
            display_time = "Unknown Date"
            if row["timestamp_parsed"] != fallback_time:
                display_time = row["timestamp_parsed"].strftime("%Y-%m-%d %H:%M")
            st.caption(f"Submitted: {display_time}")
            
            with st.expander("Patient Notes"):
                st.write(row.get("notes", "No notes provided by patient."))

        with col_risk:
            st.markdown(f"#### {status_color} {risk_level} Risk")
            st.write(f"**Score:** {row.get('risk_score', 0)}")
            st.info(row.get("ai_recommendation", "No recommendation"))

        # ================= DOCTOR NOTES =================
        doc_id = row["_doc_id"]
        
        note = st.text_input(
            "Add/Update Clinical Notes",
            value=row.get("doctor_notes", ""),
            key=f"note_{doc_id}"
        )

        if st.button("Save Note", key=f"save_{doc_id}"):
            db.collection("patients").document(doc_id).update({
                "doctor_notes": note
            })
            st.success("Note saved to patient record!")