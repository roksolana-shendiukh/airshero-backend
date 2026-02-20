import pyrebase

config = {
    "apiKey": "AIzaSyDi-wF2u8JOKzXN9-OHAwCR46y9M97TgrA",
    "authDomain": "airshero-b81e4.firebaseapp.com",
    "projectId": "airshero-b81e4",
    "storageBucket": "airshero-b81e4.firebasestorage.app",
    "messagingSenderId": "1042769401900",
    "appId": "1:1042769401900:web:e130d1d5fd01dfe0c35989",
    "databaseURL": ""
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

user = auth.sign_in_with_email_and_password("roksolana.shendiukh@gmail.com", "airsheroDB")
print(user["idToken"])