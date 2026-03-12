from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum
from sqlalchemy.orm import Session
from app.repositories import airline_repository

from app.database import get_db
from app.dependencies.auth import require_role
from app.services import admin_service

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
    agentId: Optional[int] = None
    airlineId: Optional[int] = None  # ← додай

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


@router.get("/users")
def list_users(user=Depends(require_role("systemAdmin"))):
    return admin_service.get_all_users()


@router.post("/users")
def add_user(
    body: CreateUserRequest,
    user=Depends(require_role("systemAdmin")),
):
    return admin_service.create_user(
        email=body.email,
        first_name=body.firstName,
        last_name=body.lastName,
        airline_name=body.airlineName,
        role_id=body.roleId,
        agent_id=body.agentId,
        airline_id=body.airlineId,
    )


@router.patch("/users/{uid}/role")
def update_role(
    uid: str,
    body: SetRoleRequest,
    user=Depends(require_role("systemAdmin")),
):
    admin_service.set_role(uid, body.roleId)
    return {"message": "Role updated successfully"}


@router.patch("/users/{uid}/status")
def update_status(
    uid: str,
    body: SetStatusRequest,
    user=Depends(require_role("systemAdmin")),
):
    admin_service.set_status(uid, body.status)
    return {"message": f"Status {body.status} set successfully"}


@router.get("/checkin-agents")
def list_checkin_agents(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    return admin_service.get_unassigned_checkin_agents(db)

@router.get("/airlines")
def list_airlines(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    airlines = airline_repository.get_all(db)
    return [
        {"airlineId": a.airline_id, "airlineName": a.airline_name}
        for a in airlines
    ]

