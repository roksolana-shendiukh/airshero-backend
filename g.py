import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

UID = "AFko1NsJl5NQQLnLYawzt1exzUI3"

user = auth.get_user(UID)
current_claims = user.custom_claims or {}
print(f"Current claims: {current_claims}")

current_claims["airlineId"] = 24

auth.set_custom_user_claims(UID, current_claims)
print(f"Updated! New airlineId: {current_claims['airlineId']}")