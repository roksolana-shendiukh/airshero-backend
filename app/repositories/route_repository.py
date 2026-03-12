from sqlalchemy.orm import Session, joinedload
from app.models.route_model import Route


def get_all(db: Session) -> list[Route]:
    return (
        db.query(Route)
        .options(
            joinedload(Route.departs_airport),
            joinedload(Route.arrives_airport),
        )
        .all()
    )