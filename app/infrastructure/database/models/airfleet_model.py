from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from .base import Base


class AirfleetManufacturer(Base):
    __tablename__ = "AirfleetManufacturer"

    airfleet_manufacturer_id   = Column(Integer, primary_key=True)
    airfleet_manufacturer_name = Column(String)


class Airfleet(Base):
    __tablename__ = "Airfleet"

    airfleet_id               = Column(Integer, primary_key=True)
    airfleet_manufacturer_id  = Column(Integer, ForeignKey("AirfleetManufacturer.airfleet_manufacturer_id"))
    aircraft_range_km         = Column(DECIMAL(7, 2))
    aircraft_model            = Column(String)
    aircraft_speed            = Column(DECIMAL(7, 2))
    seat_capacity             = Column(Integer)
    baggage_capacity          = Column(DECIMAL(7, 2))
    aircraft_fuel_consumption = Column(DECIMAL(6, 2))
    aircraft_url              = Column(String(255))

    manufacturer = relationship("AirfleetManufacturer")