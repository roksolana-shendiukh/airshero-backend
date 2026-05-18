"""
Запуск: python clear_operation_claim.py <uid>
Приклад: python clear_operation_claim.py hIpoJdgOvJOM2hyRKkC2Ag1JpLn1
"""
import sys
import firebase_admin
from firebase_admin import auth, credentials

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

def clear_operation(uid: str):
    user   = auth.get_user(uid)
    claims = user.custom_claims or {}
    before = claims.get("operationId")
    claims.pop("operationId", None)
    auth.set_custom_user_claims(uid, claims)
    print(f"✓ Cleared operationId={before} for uid={uid}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clear_operation_claim.py <uid>")
        sys.exit(1)
    clear_operation(sys.argv[1])