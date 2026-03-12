from sqlalchemy.orm import Session
from app.repositories import airfleet_repository
from app.schemas.airfleet_schema import AirfleetDTO


def get_all_airfleets(db: Session) -> list[AirfleetDTO]:
    return [
        AirfleetDTO(
            airfleetId=a.airfleet_id,
            aircraftModel=a.aircraft_model,
            manufacturerName=getattr(a.manufacturer, 'airfleet_manufacturer_name', None),
            seatCapacity=a.seat_capacity,
            aircraftRangeKm=float(a.aircraft_range_km) if a.aircraft_range_km else None,
        )
        for a in airfleet_repository.get_all(db)
    ]