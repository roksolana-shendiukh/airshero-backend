from __future__ import annotations

import datetime
import decimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .flight_model import Flight, FlightClass
    from .airfleet_model import Airfleet
    from .airport_model import Gate
    from .booking_model import BookingItem
    from .checkin_model import CheckInAgentFlightOperation
    from .crew_model import FlightCrewFlightOperation

from sqlalchemy import DECIMAL, Date, DateTime, ForeignKeyConstraint, Identity, Integer, PrimaryKeyConstraint, String, Time, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class FlightOperationState(Base):
    __tablename__ = 'FlightOperationState'
    __table_args__ = (
        PrimaryKeyConstraint('flight_operation_state_id', name='PK__FlightOp__E6C723964F4A5A38'),
    )

    flight_operation_state_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    flight_operation_state_description: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    FlightOperation: Mapped[list[FlightOperation]] = relationship('FlightOperation', back_populates='flight_operation_state')


class FlightOperationStatus(Base):
    __tablename__ = 'FlightOperationStatus'
    __table_args__ = (
        PrimaryKeyConstraint('flight_operation_status_id', name='PK__FlightOp__B6AA3504B74446D2'),
    )

    flight_operation_status_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    flight_operation_status_name: Mapped[Optional[str]] = mapped_column(String(10, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    FlightOperation: Mapped[list[FlightOperation]] = relationship('FlightOperation', back_populates='flight_operation_status')


class FlightStatus(Base):
    __tablename__ = 'FlightStatus'
    __table_args__ = (
        PrimaryKeyConstraint('flight_status_id', name='PK__FlightSt__C09C73A4DADDE2AF'),
    )

    flight_status_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    flight_status_name: Mapped[Optional[str]] = mapped_column(String(15, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    ScheduledFlight: Mapped[list[ScheduledFlight]] = relationship('ScheduledFlight', back_populates='flight_status')


class ScheduledFlight(Base):
    __tablename__ = 'ScheduledFlight'
    __table_args__ = (
        ForeignKeyConstraint(['flight_id'], ['Flight.flight_id'], name='FK_ScheduledFlight_Flight'),
        ForeignKeyConstraint(['flight_status_id'], ['FlightStatus.flight_status_id'], name='FK_ScheduledFlight_FlightStatus'),
        PrimaryKeyConstraint('schedule_flight_id', name='PK_ScheduledFlight'),
    )

    schedule_flight_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    flight_id: Mapped[int] = mapped_column(Integer, nullable=False)
    flight_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    departs_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    sales_start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    flight: Mapped[Flight] = relationship('Flight', back_populates='ScheduledFlight')
    flight_status: Mapped[FlightStatus] = relationship('FlightStatus', back_populates='ScheduledFlight')
    FlightOperation: Mapped[list[FlightOperation]] = relationship('FlightOperation', back_populates='schedule_flight')
    FlightPrice: Mapped[list[FlightPrice]] = relationship('FlightPrice', back_populates='schedule_flight')


class FlightOperation(Base):
    __tablename__ = 'FlightOperation'
    __table_args__ = (
        ForeignKeyConstraint(['airfleet_id'], ['Airfleet.airfleet_id'], name='FKFlightOperation_Airfleet'),
        ForeignKeyConstraint(['flight_operation_state_id'], ['FlightOperationState.flight_operation_state_id'], name='FKFlightOperation_FlightOperationState'),
        ForeignKeyConstraint(['flight_operation_status_id'], ['FlightOperationStatus.flight_operation_status_id'], name='FKFlightOperation_FlightOperationStatus'),
        ForeignKeyConstraint(['gate_id'], ['Gate.gate_id'], name='FKFlightOperation_Gate'),
        ForeignKeyConstraint(['schedule_flight_id'], ['ScheduledFlight.schedule_flight_id'], name='FK_FlightOperation_ScheduledFlight'),
        PrimaryKeyConstraint('flight_operation_id', name='PK__FlightOp__243EC266DCDCC5CB'),
    )

    flight_operation_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    schedule_flight_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('((0))'))
    airfleet_id: Mapped[Optional[int]] = mapped_column(Integer)
    gate_id: Mapped[Optional[int]] = mapped_column(Integer)
    flight_operation_status_id: Mapped[Optional[int]] = mapped_column(Integer)
    flight_operation_state_id: Mapped[Optional[int]] = mapped_column(Integer)
    actual_departure_date_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    actual_arrival_date_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    boarding_start_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    boarding_end_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    baggage_loading_start_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    baggage_loading_end_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    airfleet: Mapped[Optional[Airfleet]] = relationship('Airfleet', back_populates='FlightOperation')
    flight_operation_state: Mapped[Optional[FlightOperationState]] = relationship('FlightOperationState', back_populates='FlightOperation')
    flight_operation_status: Mapped[Optional[FlightOperationStatus]] = relationship('FlightOperationStatus', back_populates='FlightOperation')
    gate: Mapped[Optional[Gate]] = relationship('Gate', back_populates='FlightOperation')
    schedule_flight: Mapped[ScheduledFlight] = relationship('ScheduledFlight', back_populates='FlightOperation')
    CheckInAgentFlightOperation: Mapped[list[CheckInAgentFlightOperation]] = relationship('CheckInAgentFlightOperation', back_populates='flight_operation')
    FlightCrewFlightOperation: Mapped[list[FlightCrewFlightOperation]] = relationship('FlightCrewFlightOperation', back_populates='flight_operation')


class FlightPrice(Base):
    __tablename__ = 'FlightPrice'
    __table_args__ = (
        ForeignKeyConstraint(['flight_class_id'], ['FlightClass.flight_class_id'], name='FK_FlightPrice_FlightClass'),
        ForeignKeyConstraint(['schedule_flight_id'], ['ScheduledFlight.schedule_flight_id'], name='FK_FlightPrice_ScheduledFlight'),
        PrimaryKeyConstraint('flight_price_id', name='PK__FlightPr__025FD96AA6EF088A'),
    )

    flight_price_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    schedule_flight_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('((0))'))
    flight_class_id: Mapped[Optional[int]] = mapped_column(Integer)
    flight_published_date: Mapped[Optional[datetime.date]] = mapped_column(Date, server_default=text('(getdate())'))
    ticket_price: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(8, 2))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    flight_class: Mapped[Optional[FlightClass]] = relationship('FlightClass', back_populates='FlightPrice')
    schedule_flight: Mapped[ScheduledFlight] = relationship('ScheduledFlight', back_populates='FlightPrice')
    BookingItem: Mapped[list[BookingItem]] = relationship('BookingItem', back_populates='flight_price')