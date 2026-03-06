from sqlalchemy.orm import Session
from sqlalchemy import text


def search_flights(db: Session, from_city: int, to_city: int, depart_date: str):
    result = db.execute(
        text("EXEC SP_SearchFlights :departs_city_id, :arrives_city_id, :departs_date"),
        {
            "departs_city_id": from_city,
            "arrives_city_id": to_city,
            "departs_date": depart_date,
        }
    )
    return result.mappings().all()