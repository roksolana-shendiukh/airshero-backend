import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

user = auth.create_user(
    email="roksolana.shendiukh@gmail.com",
    password="airsheroDB",
    display_name="System Admin"
)

auth.set_custom_user_claims(user.uid, {
    "role": "systemAdmin",
    "status": "active"
})

print(f"Admin created: {user.uid}")