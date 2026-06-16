# 🩺 AI Healthcare MVP

A fully free-tier optimized healthcare portal connecting patients and doctors using Streamlit, Firebase, and the Gemini 2.5 AI.

## Features
* **🧑‍⚕️ Patient Portal:** Submit health metrics, and view doctor feedback.
* **🩺 Doctor Dashboard:** Secure login, auto-sorted patient risk queue (High/Moderate/Low), and clinical note-taking.
* **🧠 AI Risk Engine:** Automatically calculates health risk scores based on pain levels, steps, sleep, and mood.

## How to Run Locally
1. Clone this repository.
2. Install the requirements: `pip install -r requirements.txt`
3. Add your `serviceAccountKey.json` to the `firebase_config/` folder.
4. Run the Patient App: `streamlit run patient/patient_app.py`
5. Run the Doctor App: `streamlit run doctor/doctor_dashboard.py`




