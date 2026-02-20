from fastapi import APIRouter
from pydantic import BaseModel
import pyrebase
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

firebase = pyrebase.initialize_app({
    "apiKey": settings.FIREBASE_API_KEY,
    "authDomain": settings.FIREBASE_AUTH_DOMAIN,
    "databaseURL": "",
    "storageBucket": settings.FIREBASE_STORAGE_BUCKET
})

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(body: LoginRequest):
    user = firebase.auth().sign_in_with_email_and_password(body.email, body.password)
    return {"idToken": user["idToken"]}