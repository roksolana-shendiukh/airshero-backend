from sqlalchemy.orm import Session, joinedload
from app.models.route_model import Route


def get_all(db: Session, airline_id: int | None = None) -> list[Route]:
    query = (
        db.query(Route)
        .options(
            joinedload(Route.departs_airport),
            joinedload(Route.arrives_airport),
        )
    )
    if airline_id is not None:
        query = query.filter(Route.airline_id == airline_id)
    return query.all()

