from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from firebase_admin import auth
from app.interfaces.api.dependencies.auth import get_current_user
from app.core.services.user_service import set_status

router = APIRouter(tags=["Auth"])

class ChangePasswordRequest(BaseModel):
    password: str

@router.post("/change-password")
def change_password(body: ChangePasswordRequest, user=Depends(get_current_user)):
    from app.core.services.user_service import _validate_password
    _validate_password(body.password)
    
    try:
        auth.update_user(user["uid"], password=body.password)
        set_status(user["uid"], "active")
        return {"message": "Password changed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))