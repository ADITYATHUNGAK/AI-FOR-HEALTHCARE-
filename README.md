# Careflow — AI Healthcare MVP

Careflow is a hybrid healthcare portal. The original Streamlit applications remain the actual entry points and continue to own Firebase access, patient/doctor authentication, risk scoring, reports, clinical notes, PDF export, and the local Llama chatbot. A small React 18 presentation shell is embedded inside each Streamlit page to provide the polished visual identity without creating a second data or auth path.

## Run the original applications

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure Firebase using the existing environment variables (`FIREBASE_TYPE`, `FIREBASE_PROJECT_ID`, `FIREBASE_PRIVATE_KEY`, `FIREBASE_CLIENT_EMAIL`, and the optional certificate/URI values), or provide the existing service-account configuration expected by the project. Never commit credentials.

3. Start the patient entry point:

   ```bash
   streamlit run ai_healthcare_mvp/patient/patient_app.py
   ```

4. Start the doctor entry point in a second terminal when needed:

   ```bash
   streamlit run ai_healthcare_mvp/doctor/doctor_dashboard.py
   ```

The React shell is rendered by `ai_healthcare_mvp/ui/react_shell.py` through `streamlit.components.v1.html`. It is presentational only; all buttons, forms, Firestore operations, session state, doctor password checks, and chatbot prompts remain in the existing Streamlit code. The shell loads React 18 from the public unpkg CDN, so an internet connection is needed for that decorative header. If the CDN is unavailable, the Streamlit application and its workflows still operate.

## What remains unchanged

- Patient sign-up/login continues to use the existing `users` Firestore collection and Streamlit session state.
- Doctor login continues to use the existing `doctors` collection and password model.
- Patient reports continue to write to `patients`, with the existing risk calculator and doctor assignment.
- Doctor filtering, sorting, clinical note updates, and patient feedback remain in the original dashboard.
- The local Llama chatbot continues to use the patient app's existing model path and recent-record context.

The former Vite files in `src/` and `package.json` are retained as a design reference and optional standalone UI prototype. They are not the production entry point and are not connected to Firebase or auth. No browser Firebase credentials or duplicate API boundary were added.

## Validation

Run Python syntax validation from the repository root:

```bash
python -m py_compile ai_healthcare_mvp/utils/risk_calculator.py ai_healthcare_mvp/firebase_config/firebase_connection.py ai_healthcare_mvp/ui/react_shell.py ai_healthcare_mvp/patient/patient_app.py ai_healthcare_mvp/doctor/doctor_dashboard.py
```

The optional Vite prototype can be built with `npm install` and `npm run build` when Node.js/npm are available. The Streamlit applications do not require the Vite toolchain.
