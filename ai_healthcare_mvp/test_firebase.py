import os
import sys
from dotenv import load_dotenv

# Ensure we can import from the root directory if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from firebase_config.firebase_connection import connect_to_firestore

# Load environment variables
load_dotenv()

def run_test():
    db = connect_to_firestore()

    if not db:
        print("❌ Firestore connection failed")
        sys.exit()

    try:
        # Write test data
        test_ref = db.collection("test_data").document("connection_test")
        
        print("⏳ Writing to Firestore...")
        test_ref.set({
            "status": "success",
            "message": "Firebase is working",
        })
        print("✅ Firestore WRITE SUCCESS")

        # Read it back (IMPORTANT DEBUG STEP)
        print("⏳ Reading from Firestore...")
        doc = test_ref.get()

        if doc.exists:
            print(f"✅ Firestore READ SUCCESS: {doc.to_dict()}")
        else:
            print("❌ Document not found after writing")

        # Cleanup test artifact
        print("🧹 Cleaning up test data...")
        test_ref.delete()
        print("✅ Cleanup SUCCESS. Database is clean.")

    except Exception as e:
        print(f"❌ Firestore error: {e}")

if __name__ == "__main__":
    run_test()