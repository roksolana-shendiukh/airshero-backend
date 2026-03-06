from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum
from firebase_admin import auth
from app.dependencies.auth import require_role, get_current_user
from app.services.user_service import get_all_users, create_user, set_role, set_status
from app.models.checkin_model import CheckInAgent
from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy.orm import joinedload

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
    agentId: Optional[int] = None  # обов'язковий якщо roleId == 2 (checkInAgent)

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
        agent_id=body.agentId, 
    )


@router.patch("/users/{uid}/role")
def update_role(uid: str, body: SetRoleRequest, user=Depends(require_role("systemAdmin"))):
    set_role(uid, body.roleId)
    return {"message": "Role updated successfully"}


@router.patch("/users/{uid}/status")
def update_status(uid: str, body: SetStatusRequest, user=Depends(require_role("systemAdmin"))):
    set_status(uid, body.status)
    return {"message": f"Status {body.status} set successfully"}

@router.get("/checkin-agents")
def list_checkin_agents(
    db: Session = Depends(get_db),
    user=Depends(require_role("systemAdmin")),
):
    used_agent_ids = set()
    page = auth.list_users()
    while page:
        for u in page.users:
            claims = u.custom_claims or {}
            agent_id = claims.get("agentId")
            if agent_id is not None:
                used_agent_ids.add(agent_id)
        page = page.get_next_page()

    agents = (
        db.query(CheckInAgent)
        .options(joinedload(CheckInAgent.airport))
        .all()
    )
    return [
        {
            "agentId":     a.checkin_agent_id,
            "firstName":   a.checkin_agent_first_name,
            "lastName":    a.checkin_agent_last_name,
            "phoneNumber": a.checkin_agent_phone_number,
            "airportCode": getattr(a.airport, "airport_code", None),
            "airportName": getattr(a.airport, "airport_name", None),
        }
        for a in agents
        if a.checkin_agent_id not in used_agent_ids
    ]

