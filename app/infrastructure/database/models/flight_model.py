from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL, Date
from sqlalchemy.orm import relationship
from .base import Base


class FlightStatus(Base):
    __tablename__ = "FlightStatus"

    flight_status_id   = Column(Integer, primary_key=True)
    flight_status_name = Column(String)


class Class(Base):
    __tablename__ = "Class"

    class_id   = Column(Integer, primary_key=True)
    class_name = Column(String)


class Flight(Base):
    __tablename__ = "Flight"

    flight_id          = Column(Integer, primary_key=True)
    flight_status_id   = Column(Integer, ForeignKey("FlightStatus.flight_status_id"))
    flight_schedule_id = Column(Integer, ForeignKey("FlightSchedule.flight_schedule_id"))
    departs_datetime   = Column(DateTime)
    arrives_datetime   = Column(DateTime)

    flight_status   = relationship("FlightStatus")
    flight_schedule = relationship("FlightSchedule")
    flight_classes  = relationship("FlightClass", back_populates="flight")


class FlightClass(Base):
    __tablename__ = "FlightClass"

    flight_class_id = Column(Integer, primary_key=True)
    class_id        = Column(Integer, ForeignKey("Class.class_id"))
    flight_id       = Column(Integer, ForeignKey("Flight.flight_id"))

    flight = relationship("Flight", back_populates="flight_classes")
    cls    = relationship("Class")
    prices = relationship("FlightPrice", back_populates="flight_class")


class FlightPrice(Base):
    __tablename__ = "FlightPrice"

    flight_price_id       = Column(Integer, primary_key=True)
    flight_class_id       = Column(Integer, ForeignKey("FlightClass.flight_class_id"))
    flight_published_date = Column(Date)
    ticket_price          = Column(DECIMAL(8, 2))

    flight_class = relationship("FlightClass", back_populates="prices")