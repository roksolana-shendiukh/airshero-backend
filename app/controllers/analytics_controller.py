from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies.auth import require_role
from app.database import get_db
from app.services.analytics_service import get_active_users, get_top_events, get_screen_views
from app.services.system_service import (
    get_server_stats,
    get_db_stats,
    get_firebase_user_stats,
    get_server_history,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
_admin = Depends(require_role("systemAdmin"))


@router.get("/active-users", dependencies=[_admin])
def active_users():
    return get_active_users()


@router.get("/events", dependencies=[_admin])
def top_events():
    return get_top_events()


@router.get("/screens", dependencies=[_admin])
def screen_views():
    return get_screen_views()


@router.get("/system", dependencies=[_admin])
def system_analytics(db: Session = Depends(get_db)):
    return {
        "server": get_server_stats(),
        "database": get_db_stats(db),
        "users": get_firebase_user_stats(),
    }


@router.get("/system/history", dependencies=[_admin])
def system_history():
    return {"data": get_server_history()}