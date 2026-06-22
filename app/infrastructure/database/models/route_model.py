from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Time
from sqlalchemy.orm import relationship
from .base import Base


class Route(Base):
    __tablename__ = "Route"

    route_id           = Column(Integer, primary_key=True)
    airline_id         = Column(Integer, ForeignKey("Airline.airline_id"))
    airfleet_id        = Column(Integer, ForeignKey("Airfleet.airfleet_id"))
    departs_airport_id = Column(Integer, ForeignKey("Airport.airport_id"))
    arrives_airport_id = Column(Integer, ForeignKey("Airport.airport_id"))
    flight_number      = Column(String, unique=True)
    flight_range       = Column(DECIMAL(7, 2))
    flight_duration    = Column(Time)

    airline         = relationship("Airline")
    departs_airport = relationship("Airport", foreign_keys=[departs_airport_id])
    arrives_airport = relationship("Airport", foreign_keys=[arrives_airport_id])