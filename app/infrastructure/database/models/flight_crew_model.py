from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class FlightCrewPosition(Base):
    __tablename__ = "FlightCrewPosition"

    flight_crew_position_id   = Column(Integer, primary_key=True)
    flight_crew_position_name = Column(String)


class FlightCrewLicenseType(Base):
    __tablename__ = "FlightCrewLicenseType"

    flight_crew_license_type_id   = Column(Integer, primary_key=True)
    flight_crew_license_type_name = Column(String)


class FlightCrew(Base):
    __tablename__ = "FlightCrew"

    flight_crew_id              = Column(Integer, primary_key=True)
    flight_crew_position_id     = Column(Integer, ForeignKey("FlightCrewPosition.flight_crew_position_id"))
    flight_crew_license_type    = Column(Integer, ForeignKey("FlightCrewLicenseType.flight_crew_license_type_id"))
    flight_crew_first_name      = Column(String)
    flight_crew_last_name       = Column(String)
    flight_crew_experience_years = Column(Integer)

    position     = relationship("FlightCrewPosition")
    license_type = relationship("FlightCrewLicenseType")


class AirfleetFlightCrew(Base):
    __tablename__ = "AirfleetFlightCrew"

    airfleet_id     = Column(Integer, ForeignKey("Airfleet.airfleet_id"), primary_key=True)
    flight_crew_id  = Column(Integer, ForeignKey("FlightCrew.flight_crew_id"), primary_key=True)


class FlightCrewFlightOperation(Base):
    __tablename__ = "FlightCrewFlightOperation"

    flight_crew_id      = Column(Integer, ForeignKey("FlightCrew.flight_crew_id"), primary_key=True)
    flight_operation_id = Column(Integer, ForeignKey("FlightOperation.flight_operation_id"), primary_key=True)

    crew      = relationship("FlightCrew")
    operation = relationship("FlightOperation")