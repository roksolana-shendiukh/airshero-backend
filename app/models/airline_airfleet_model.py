from sqlalchemy import Column, Integer, ForeignKey
from .base import Base


class AirlineAirfleet(Base):
    __tablename__ = "AirlineAirfleet"

    airline_id  = Column(Integer, ForeignKey("Airline.airline_id"), primary_key=True)
    airfleet_id = Column(Integer, ForeignKey("Airfleet.airfleet_id"), primary_key=True)