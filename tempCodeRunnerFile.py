import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

uid = "hEeW3b7zk1P8O8CK6lsRCVPtkOe2"

auth.set_custom_user_claims(uid, {
    "role": "systemAdmin",
    "status": "active"
})

print("Done!")