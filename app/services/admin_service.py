from sqlalchemy.orm import Session, joinedload
from firebase_admin import auth
from app.models.checkin_model import CheckInAgent


def get_all_users() -> list[dict]:
    from app.services.user_service import get_all_users as _get_all
    return _get_all()


def create_user(
    email: str,
    first_name: str,
    last_name: str,
    airline_name: str,
    role_id: int,
    agent_id: int | None,
    airline_id: int | None = None,
) -> dict:
    from app.services.user_service import create_user as _create
    return _create(
        email=email,
        first_name=first_name,
        last_name=last_name,
        airline_name=airline_name,
        role_id=role_id,
        agent_id=agent_id,
        airline_id=airline_id, 
    )


def set_role(uid: str, role_id: int) -> None:
    from app.services.user_service import set_role as _set_role
    _set_role(uid, role_id)


def set_status(uid: str, status: str) -> None:
    from app.services.user_service import set_status as _set_status
    _set_status(uid, status)


def get_unassigned_checkin_agents(db: Session) -> list[dict]:
    used_agent_ids: set[int] = set()
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