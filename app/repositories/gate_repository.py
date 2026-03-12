from sqlalchemy.orm import Session, joinedload
from app.models.gate_model import Gate
from app.models.terminal_model import Terminal


def get_all(db: Session, airport_id: int | None = None) -> list[Gate]:
    query = (
        db.query(Gate)
        .options(joinedload(Gate.terminal))
        .join(Gate.terminal)
    )
    if airport_id is not None:
        query = query.filter(Terminal.airport_id == airport_id)
    return query.all()