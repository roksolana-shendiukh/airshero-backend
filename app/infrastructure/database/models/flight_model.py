from __future__ import annotations

import datetime
import decimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .airfleet_model import Airfleet
    from .airline_model import Airline
    from .airport_model import Airport
    from .seat_model import Class
    from .crew_model import FlightCrew
    from .flight_operation_model import FlightPrice, ScheduledFlight
    from .flight_schedule_model import FlightSchedule
    from .baggage_model import BaggagePricingInFlight

from sqlalchemy import Boolean, DECIMAL, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Time, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Route(Base):
    __tablename__ = 'Route'
    __table_args__ = (
        ForeignKeyConstraint(['arrives_airport_id'], ['Airport.airport_id'], name='FK_Route_AirportA'),
        ForeignKeyConstraint(['departs_airport_id'], ['Airport.airport_id'], name='FK_Route_AirportD'),
        PrimaryKeyConstraint('route_id', name='PK__Route__28F706FED0D5CF9A'),
    )

    route_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    departs_airport_id: Mapped[Optional[int]] = mapped_column(Integer)
    arrives_airport_id: Mapped[Optional[int]] = mapped_column(Integer)
    flight_range: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(7, 2))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    arrives_airport: Mapped[Optional[Airport]] = relationship('Airport', foreign_keys=[arrives_airport_id], back_populates='Route_arrives_airport')
    departs_airport: Mapped[Optional[Airport]] = relationship('Airport', foreign_keys=[departs_airport_id], back_populates='Route_departs_airport')
    Flight: Mapped[list[Flight]] = relationship('Flight', back_populates='route')


class Flight(Base):
    __tablename__ = 'Flight'
    __table_args__ = (
        ForeignKeyConstraint(['airfleet_id'], ['Airfleet.airfleet_id'], name='FK_Flight_Airfleet'),
        ForeignKeyConstraint(['airline_id'], ['Airline.airline_id'], name='FK_Flight_Airline'),
        ForeignKeyConstraint(['route_id'], ['Route.route_id'], name='FK_Flight_Route'),
        PrimaryKeyConstraint('flight_id', name='PK__Flight__E37057651C15B469'),
    )

    flight_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    airline_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('((0))'))
    route_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('((0))'))
    airfleet_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('((0))'))
    flight_number: Mapped[str] = mapped_column(String(7, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False, server_default=text("('')"))
    flight_duration: Mapped[datetime.time] = mapped_column(Time, nullable=False, server_default=text("('00:00:00')"))
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('((0))'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    airfleet: Mapped[Airfleet] = relationship('Airfleet', back_populates='Flight')
    airline: Mapped[Airline] = relationship('Airline', back_populates='Flight')
    route: Mapped[Route] = relationship('Route', back_populates='Flight')
    FlightClass: Mapped[list[FlightClass]] = relationship('FlightClass', back_populates='flight')
    FlightFlightCrew: Mapped[list[FlightFlightCrew]] = relationship('FlightFlightCrew', back_populates='flight')
    FlightSchedule: Mapped[list[FlightSchedule]] = relationship('FlightSchedule', back_populates='flight')
    ScheduledFlight: Mapped[list[ScheduledFlight]] = relationship('ScheduledFlight', back_populates='flight')


class FlightClass(Base):
    __tablename__ = 'FlightClass'
    __table_args__ = (
        ForeignKeyConstraint(['class_id'], ['Class.class_id'], name='FKFlightClass_Class'),
        ForeignKeyConstraint(['flight_id'], ['Flight.flight_id'], name='FK_FlightClass_Flight'),
        PrimaryKeyConstraint('flight_class_id', name='PK__FlightCl__69CC4634AD1F9274'),
        Index('UQ_FlightClass_Class_Flight', 'class_id', 'flight_id', mssql_clustered=False, unique=True),
    )

    flight_class_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    class_id: Mapped[Optional[int]] = mapped_column(Integer)
    flight_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    class_: Mapped[Optional[Class]] = relationship('Class', back_populates='FlightClass')
    flight: Mapped[Optional[Flight]] = relationship('Flight', back_populates='FlightClass')
    BaggagePricingInFlight: Mapped[list[BaggagePricingInFlight]] = relationship('BaggagePricingInFlight', back_populates='flight_class')
    FlightPrice: Mapped[list[FlightPrice]] = relationship('FlightPrice', back_populates='flight_class')


class FlightFlightCrew(Base):
    __tablename__ = 'FlightFlightCrew'
    __table_args__ = (
        ForeignKeyConstraint(['flight_crew_id'], ['FlightCrew.flight_crew_id'], name='FK_Flight_FlightCrew_FlightCrew'),
        ForeignKeyConstraint(['flight_id'], ['Flight.flight_id'], name='FK_Flight_FlightCrew_Flight'),
        PrimaryKeyConstraint('flight_flight_crew', name='PK_Flight_FlightCrew'),
    )

    flight_flight_crew: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    flight_id: Mapped[int] = mapped_column(Integer, nullable=False)
    flight_crew_id: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('((1))'))

    flight_crew: Mapped[FlightCrew] = relationship('FlightCrew', back_populates='FlightFlightCrew')
    flight: Mapped[Flight] = relationship('Flight', back_populates='FlightFlightCrew')


    