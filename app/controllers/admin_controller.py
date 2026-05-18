from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.database import get_db
from app.dependencies.auth import require_role
from app.repositories import airline_repository
from app.services import admin_service
from app.schemas.admin_schema import (
    CreateUserRequest,
    SetRoleRequest,
    SetStatusRequest,
    SetOperationRequest,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


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


@router.delete("/users/{uid}")  
def delete_user(
    uid: str,
    user=Depends(require_role("systemAdmin")),
):
    try:
        from firebase_admin import auth
        auth.delete_user(uid)
        return {"message": "User deleted successfully"}
    except Exception as e:        
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/users/{uid}/status")
def update_status(
    uid: str,
    body: SetStatusRequest,
    user=Depends(require_role("systemAdmin")),
):
    admin_service.set_status(uid, body.status)
    return {"message": f"Status {body.status} set successfully"}


@router.patch("/users/{uid}/operation")
def set_operation(
    uid: str,
    body: SetOperationRequest,
    user=Depends(require_role("systemAdmin")),
):
    admin_service.set_operation(uid, body.operationId)
    return {"message": "Operation assigned successfully"}


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



