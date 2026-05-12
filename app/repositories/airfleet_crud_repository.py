from sqlalchemy.orm import Session
from app.models.airfleet_model import Airfleet, AirfleetManufacturer
from app.models.seat_model import SeatLayout, SeatType
from app.models.flight_model import Class

def get_all_manufacturers(db: Session) -> list:
    return db.query(AirfleetManufacturer).order_by(
        AirfleetManufacturer.airfleet_manufacturer_name).all()

def get_manufacturer(db: Session, manufacturer_id: int) -> AirfleetManufacturer | None:
    return db.query(AirfleetManufacturer).filter(
        AirfleetManufacturer.airfleet_manufacturer_id == manufacturer_id).first()

def create_manufacturer(db: Session, name: str) -> AirfleetManufacturer:
    obj = AirfleetManufacturer(airfleet_manufacturer_name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_manufacturer(db: Session, manufacturer_id: int,
                        name: str) -> AirfleetManufacturer | None:
    obj = get_manufacturer(db, manufacturer_id)
    if not obj:
        return None
    obj.airfleet_manufacturer_name = name
    db.commit()
    db.refresh(obj)
    return obj

def delete_manufacturer(db: Session, manufacturer_id: int) -> bool:
    obj = get_manufacturer(db, manufacturer_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def get_all_airfleets(db: Session) -> list:
    return db.query(Airfleet).join(AirfleetManufacturer).order_by(
        Airfleet.aircraft_model).all()

def get_airfleet(db: Session, airfleet_id: int) -> Airfleet | None:
    return db.query(Airfleet).filter(
        Airfleet.airfleet_id == airfleet_id).first()

def create_airfleet(
    db: Session,
    airfleet_manufacturer_id: int,
    aircraft_model: str,
    aircraft_range_km: float,
    aircraft_speed: float,
    seat_capacity: int,
    baggage_capacity: float,
    aircraft_fuel_consumption: float | None,
    aircraft_url: str | None,
) -> Airfleet:
    obj = Airfleet(
        airfleet_manufacturer_id=airfleet_manufacturer_id,
        aircraft_model=aircraft_model,
        aircraft_range_km=aircraft_range_km,
        aircraft_speed=aircraft_speed,
        seat_capacity=seat_capacity,
        baggage_capacity=baggage_capacity,
        aircraft_fuel_consumption=aircraft_fuel_consumption,
        aircraft_url=aircraft_url,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_airfleet(
    db: Session,
    airfleet_id: int,
    airfleet_manufacturer_id: int,
    aircraft_model: str,
    aircraft_range_km: float,
    aircraft_speed: float,
    seat_capacity: int,
    baggage_capacity: float,
    aircraft_fuel_consumption: float | None,
    aircraft_url: str | None,
) -> Airfleet | None:
    obj = get_airfleet(db, airfleet_id)
    if not obj:
        return None
    obj.airfleet_manufacturer_id = airfleet_manufacturer_id
    obj.aircraft_model = aircraft_model
    obj.aircraft_range_km = aircraft_range_km
    obj.aircraft_speed = aircraft_speed
    obj.seat_capacity = seat_capacity
    obj.baggage_capacity = baggage_capacity
    obj.aircraft_fuel_consumption = aircraft_fuel_consumption
    obj.aircraft_url = aircraft_url
    db.commit()
    db.refresh(obj)
    return obj

def delete_airfleet(db: Session, airfleet_id: int) -> bool:
    obj = get_airfleet(db, airfleet_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def get_seat_layouts_for_airfleet(db: Session, airfleet_id: int) -> list:
    return db.query(SeatLayout).filter(
        SeatLayout.airfleet_id == airfleet_id
    ).order_by(SeatLayout.seat_layout_rows).all()

def get_seat_layout(db: Session, seat_layout_id: int) -> SeatLayout | None:
    return db.query(SeatLayout).filter(
        SeatLayout.seat_layout_id == seat_layout_id).first()

def create_seat_layout(
    db: Session,
    airfleet_id: int,
    class_id: int,
    seat_type_id: int,
    seat_layout_rows: int,
    seat_layout_columns: str,
) -> SeatLayout:
    obj = SeatLayout(
        airfleet_id=airfleet_id,
        class_id=class_id,
        seat_type_id=seat_type_id,
        seat_layout_rows=seat_layout_rows,
        seat_layout_columns=seat_layout_columns,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_seat_layout(
    db: Session,
    seat_layout_id: int,
    class_id: int,
    seat_type_id: int,
    seat_layout_rows: int,
    seat_layout_columns: str,
) -> SeatLayout | None:
    obj = get_seat_layout(db, seat_layout_id)
    if not obj:
        return None
    obj.class_id = class_id
    obj.seat_type_id = seat_type_id
    obj.seat_layout_rows = seat_layout_rows
    obj.seat_layout_columns = seat_layout_columns
    db.commit()
    db.refresh(obj)
    return obj

def delete_seat_layout(db: Session, seat_layout_id: int) -> bool:
    obj = get_seat_layout(db, seat_layout_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def delete_all_seat_layouts_for_airfleet(db: Session, airfleet_id: int) -> None:
    db.query(SeatLayout).filter(
        SeatLayout.airfleet_id == airfleet_id).delete()
    db.commit()

def get_all_seat_types(db: Session) -> list:
    return db.query(SeatType).order_by(SeatType.seat_type_name).all()