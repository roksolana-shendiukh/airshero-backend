from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum
from firebase_admin import auth
from app.dependencies.auth import require_role, get_current_user
from app.services.user_service import get_all_users, create_user, set_role, set_status

router = APIRouter(prefix="/admin", tags=["Admin"])

class UserStatus(str, Enum):
    pendingActivation = "pendingActivation"
    active = "active"
    locked = "locked"

class CreateUserRequest(BaseModel):
    email: EmailStr
    firstName: str
    lastName: str
    airlineName: str
    roleId: int

    @field_validator("firstName", "lastName", "airlineName")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        if len(v) > 50:
            raise ValueError("Field cannot exceed 50 characters")
        return v.strip()

class SetRoleRequest(BaseModel):
    roleId: int

class SetStatusRequest(BaseModel):
    status: UserStatus

class ChangePasswordRequest(BaseModel):
    password: str

@router.get("/users")
def list_users(user=Depends(require_role("systemAdmin"))):
    return get_all_users()

@router.post("/users")
def add_user(body: CreateUserRequest, user=Depends(require_role("systemAdmin"))):
    return create_user(
        email=body.email,
        first_name=body.firstName,
        last_name=body.lastName,
        airline_name=body.airlineName,
        role_id=body.roleId,
    )

@router.patch("/users/{uid}/role")
def update_role(uid: str, body: SetRoleRequest, user=Depends(require_role("systemAdmin"))):
    set_role(uid, body.roleId)
    return {"message": f"Role updated successfully"}

@router.patch("/users/{uid}/status")
def update_status(uid: str, body: SetStatusRequest, user=Depends(require_role("systemAdmin"))):
    set_status(uid, body.status)
    return {"message": f"Status {body.status} set successfully"}


