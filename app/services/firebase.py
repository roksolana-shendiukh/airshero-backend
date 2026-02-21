import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

def verify_token(token: str) -> dict:
    try:
        decoded = auth.verify_id_token(token, clock_skew_seconds=5)
        return decoded
    except Exception as e:
        print(f"verify_token error: {type(e).__name__}: {e}")
        raise