import os
import firebase_admin
from firebase_admin import credentials, firestore

def connect_to_firestore():
    try:
        # ================= ALREADY INITIALIZED =================
        if firebase_admin._apps:
            return firestore.client()

        # ================= VALIDATE ENV =================
        required_vars = [
            "FIREBASE_TYPE",
            "FIREBASE_PROJECT_ID",
            "FIREBASE_PRIVATE_KEY",
            "FIREBASE_CLIENT_EMAIL",
        ]

        missing = [v for v in required_vars if not os.getenv(v)]
        if missing:
            print(f"❌ Missing Firebase env vars: {missing}")
            return None

        # ================= BUILD CREDENTIALS =================
        # Build the dictionary directly from environment variables.
        firebase_creds = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
        }

        # ================= INIT FIREBASE =================
        # Pass the dictionary directly to the Certificate method. 
        # No disk writing is required.
        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)

        print("🔥 Firebase initialized successfully")

        return firestore.client()

    except Exception as e:
        print(f"❌ Firebase connection error: {e}")
        return None