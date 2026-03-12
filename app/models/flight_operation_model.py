from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


class FlightOperationStatus(Base):
    __tablename__ = "FlightOperationStatus"

    flight_operation_status_id   = Column(Integer, primary_key=True)
    flight_operation_status_name = Column(String)


class FlightOperation(Base):
    __tablename__ = "FlightOperation"

    flight_operation_id        = Column(Integer, primary_key=True)
    flight_id                  = Column(Integer, ForeignKey("Flight.flight_id"), unique=True)
    flight_operation_status_id = Column(Integer, ForeignKey("FlightOperationStatus.flight_operation_status_id"))
    airfleet_id                = Column(Integer, ForeignKey("Airfleet.airfleet_id"))
    gate_id                    = Column(Integer, ForeignKey("Gate.gate_id"))
    actual_departure_date_time = Column(DateTime)
    actual_arrival_date_time   = Column(DateTime)
    boarding_start_time        = Column(DateTime)
    boarding_end_time          = Column(DateTime)
    baggage_loading_start_time = Column(DateTime)
    baggage_loading_end_time   = Column(DateTime)

    flight   = relationship("Flight")
    status   = relationship("FlightOperationStatus")
    airfleet = relationship("Airfleet")
    gate     = relationship("Gate")