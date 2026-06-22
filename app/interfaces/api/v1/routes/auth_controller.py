from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from firebase_admin import auth
import pyrebase
from app.config import settings
from app.interfaces.api.dependencies.auth import get_current_user
from app.core.services.user_service import set_status, _validate_password

router = APIRouter(tags=["Auth"])

firebase = pyrebase.initialize_app({
    "apiKey":        settings.FIREBASE_API_KEY,
    "authDomain":    settings.FIREBASE_AUTH_DOMAIN,
    "databaseURL":   "",
    "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
})


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    password: str


@router.post("/auth/login")
def login(body: LoginRequest):
    user = firebase.auth().sign_in_with_email_and_password(body.email, body.password)
    return {"idToken": user["idToken"]}


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, user=Depends(get_current_user)):
    _validate_password(body.password)
    try:
        auth.update_user(user["uid"], password=body.password)
        set_status(user["uid"], "active")
        return {"message": "Password changed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))