from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .airline_model import Airline
    from .airfleet_model import Airfleet, AirfleetFlightCrew
    from .flight_model import FlightFlightCrew
    from .flight_operation_model import FlightOperation

from sqlalchemy import Boolean, ForeignKeyConstraint, Identity, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class FlightCrewLicenseType(Base):
    __tablename__ = 'FlightCrewLicenseType'
    __table_args__ = (
        PrimaryKeyConstraint('flight_crew_license_type_id', name='PK__FlightCr__DD36C07B63004E27'),
    )

    flight_crew_license_type_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    flight_crew_license_type_name: Mapped[Optional[str]] = mapped_column(String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    FlightCrew: Mapped[list[FlightCrew]] = relationship('FlightCrew', back_populates='FlightCrewLicenseType_')


class FlightCrewPosition(Base):
    __tablename__ = 'FlightCrewPosition'
    __table_args__ = (
        PrimaryKeyConstraint('flight_crew_position_id', name='PK__FlightCr__6123FD44423D9585'),
    )

    flight_crew_position_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    flight_crew_position_name: Mapped[Optional[str]] = mapped_column(String(40, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    FlightCrew: Mapped[list[FlightCrew]] = relationship('FlightCrew', back_populates='flight_crew_position')


class FlightCrew(Base):
    __tablename__ = 'FlightCrew'
    __table_args__ = (
        ForeignKeyConstraint(['airline_id'], ['Airline.airline_id'], name='FK_FlightCrew_Airline'),
        ForeignKeyConstraint(['flight_crew_license_type'], ['FlightCrewLicenseType.flight_crew_license_type_id'], name='FKFlightCrew_FlightCrewLicenseType'),
        ForeignKeyConstraint(['flight_crew_position_id'], ['FlightCrewPosition.flight_crew_position_id'], name='FKFlightCrew_FlightCrewPosition'),
        PrimaryKeyConstraint('flight_crew_id', name='PK__FlightCr__219127C1EC917416'),
    )

    flight_crew_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    airline_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('((0))'))
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('((0))'))
    flight_crew_position_id: Mapped[Optional[int]] = mapped_column(Integer)
    flight_crew_license_type: Mapped[Optional[int]] = mapped_column(Integer)
    flight_crew_first_name: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    flight_crew_last_name: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    flight_crew_experience_years: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    airline: Mapped[Airline] = relationship('Airline', back_populates='FlightCrew')
    FlightCrewLicenseType_: Mapped[Optional[FlightCrewLicenseType]] = relationship('FlightCrewLicenseType', back_populates='FlightCrew')
    flight_crew_position: Mapped[Optional[FlightCrewPosition]] = relationship('FlightCrewPosition', back_populates='FlightCrew')
    AirfleetFlightCrew: Mapped[list[AirfleetFlightCrew]] = relationship('AirfleetFlightCrew', back_populates='flight_crew')
    FlightFlightCrew: Mapped[list[FlightFlightCrew]] = relationship('FlightFlightCrew', back_populates='flight_crew')
    FlightCrewFlightOperation: Mapped[list[FlightCrewFlightOperation]] = relationship('FlightCrewFlightOperation', back_populates='flight_crew')


class FlightCrewFlightOperation(Base):
    __tablename__ = 'FlightCrewFlightOperation'
    __table_args__ = (
        ForeignKeyConstraint(['flight_crew_id'], ['FlightCrew.flight_crew_id'], name='FKFlightCrew_FlightCrew'),
        ForeignKeyConstraint(['flight_operation_id'], ['FlightOperation.flight_operation_id'], name='FKFlightOperation_FlightOperation'),
        PrimaryKeyConstraint('flight_crew_id', 'flight_operation_id', name='PK__FlightCr__53D2CBE7A5C4E0B4'),
    )

    flight_crew_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_operation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    flight_crew: Mapped[FlightCrew] = relationship('FlightCrew', back_populates='FlightCrewFlightOperation')
    flight_operation: Mapped[FlightOperation] = relationship('FlightOperation', back_populates='FlightCrewFlightOperation')