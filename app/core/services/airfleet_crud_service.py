from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.infrastructure.database.repositories import airfleet_crud_repository as repo


def _map_seat_layout(sl) -> dict:
    return {
        "seat_layout_id":      sl.seat_layout_id,
        "class_id":            sl.class_id,
        "class_name":          sl.cls.class_name if sl.cls else None,
        "seat_type_id":        sl.seat_type_id,
        "seat_type_name":      sl.seat_type.seat_type_name if sl.seat_type else None,
        "seat_layout_rows":    sl.seat_layout_rows,
        "seat_layout_columns": sl.seat_layout_columns,
    }


def _map_airfleet(a, layouts) -> dict:
    return {
        "airfleet_id":               a.airfleet_id,
        "aircraft_model":            a.aircraft_model,
        "aircraft_range_km":         float(a.aircraft_range_km) if a.aircraft_range_km else None,
        "aircraft_speed":            float(a.aircraft_speed) if a.aircraft_speed else None,
        "seat_capacity":             a.seat_capacity,
        "baggage_capacity":          float(a.baggage_capacity) if a.baggage_capacity else None,
        "aircraft_fuel_consumption": float(a.aircraft_fuel_consumption) if a.aircraft_fuel_consumption else None,
        "aircraft_url":              a.aircraft_url,
        "manufacturer_id":           a.airfleet_manufacturer_id,
        "manufacturer_name":         a.manufacturer.airfleet_manufacturer_name if a.manufacturer else None,
        "seat_layouts":              [_map_seat_layout(sl) for sl in layouts],
    }


def get_all_manufacturers(db: Session) -> list:
    return [
        {
            "manufacturer_id":   m.airfleet_manufacturer_id,
            "manufacturer_name": m.airfleet_manufacturer_name,
        }
        for m in repo.get_all_manufacturers(db)
    ]


def create_manufacturer(db: Session, name: str) -> dict:
    obj = repo.create_manufacturer(db, name.strip())
    return {
        "manufacturer_id":   obj.airfleet_manufacturer_id,
        "manufacturer_name": obj.airfleet_manufacturer_name,
    }


def update_manufacturer(db: Session, manufacturer_id: int, name: str) -> dict:
    obj = repo.update_manufacturer(db, manufacturer_id, name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return {
        "manufacturer_id":   obj.airfleet_manufacturer_id,
        "manufacturer_name": obj.airfleet_manufacturer_name,
    }


def delete_manufacturer(db: Session, manufacturer_id: int) -> dict:
    if not repo.delete_manufacturer(db, manufacturer_id):
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return {"deleted": True}


def get_all_airfleets(db: Session) -> list:
    return [
        _map_airfleet(a, repo.get_seat_layouts_for_airfleet(db, a.airfleet_id))
        for a in repo.get_all_airfleets(db)
    ]


def get_airfleet(db: Session, airfleet_id: int) -> dict:
    a = repo.get_airfleet(db, airfleet_id)
    if not a:
        raise HTTPException(status_code=404, detail="Airfleet not found")
    layouts = repo.get_seat_layouts_for_airfleet(db, airfleet_id)
    return _map_airfleet(a, layouts)


def create_airfleet(
    db: Session,
    airfleet_manufacturer_id:  int,
    aircraft_model:            str,
    aircraft_range_km:         float,
    aircraft_speed:            float,
    seat_capacity:             int,
    baggage_capacity:          float,
    aircraft_fuel_consumption: float | None,
    aircraft_url:              str | None,
) -> dict:
    obj = repo.create_airfleet(
        db, airfleet_manufacturer_id, aircraft_model,
        aircraft_range_km, aircraft_speed, seat_capacity,
        baggage_capacity, aircraft_fuel_consumption, aircraft_url,
    )
    return {"airfleet_id": obj.airfleet_id, "aircraft_model": obj.aircraft_model}


def update_airfleet(
    db: Session,
    airfleet_id:               int,
    airfleet_manufacturer_id:  int,
    aircraft_model:            str,
    aircraft_range_km:         float,
    aircraft_speed:            float,
    seat_capacity:             int,
    baggage_capacity:          float,
    aircraft_fuel_consumption: float | None,
    aircraft_url:              str | None,
) -> dict:
    obj = repo.update_airfleet(
        db, airfleet_id, airfleet_manufacturer_id, aircraft_model,
        aircraft_range_km, aircraft_speed, seat_capacity,
        baggage_capacity, aircraft_fuel_consumption, aircraft_url,
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Airfleet not found")
    return {"airfleet_id": obj.airfleet_id, "aircraft_model": obj.aircraft_model}


def delete_airfleet(db: Session, airfleet_id: int) -> dict:
    if not repo.delete_airfleet(db, airfleet_id):
        raise HTTPException(status_code=404, detail="Airfleet not found")
    return {"deleted": True}


def get_seat_types(db: Session) -> list:
    return [
        {"seat_type_id": st.seat_type_id, "seat_type_name": st.seat_type_name}
        for st in repo.get_all_seat_types(db)
    ]


def create_seat_layout(
    db: Session,
    airfleet_id:         int,
    class_id:            int,
    seat_type_id:        int,
    seat_layout_rows:    int,
    seat_layout_columns: str,
) -> dict:
    obj = repo.create_seat_layout(
        db, airfleet_id, class_id, seat_type_id,
        seat_layout_rows, seat_layout_columns,
    )
    return {"seat_layout_id": obj.seat_layout_id}


def update_seat_layout(
    db: Session,
    seat_layout_id:      int,
    class_id:            int,
    seat_type_id:        int,
    seat_layout_rows:    int,
    seat_layout_columns: str,
) -> dict:
    obj = repo.update_seat_layout(
        db, seat_layout_id, class_id, seat_type_id,
        seat_layout_rows, seat_layout_columns,
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Seat layout not found")
    return {"seat_layout_id": obj.seat_layout_id}


def delete_seat_layout(db: Session, seat_layout_id: int) -> dict:
    if not repo.delete_seat_layout(db, seat_layout_id):
        raise HTTPException(status_code=404, detail="Seat layout not found")
    return {"deleted": True}