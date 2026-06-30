from __future__ import annotations

import datetime
import decimal
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .airline_model import AirlineAirfleet
    from .crew_model import FlightCrew
    from .airfleet_model import AirfleetFlightCrew 
    from .flight_model import Flight
    from .flight_operation_model import FlightOperation
    from .seat_model import SeatLayout

from sqlalchemy import Computed, DECIMAL, ForeignKeyConstraint, Identity, Integer, PrimaryKeyConstraint, String, Unicode, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class AirfleetManufacturer(Base):
    __tablename__ = 'AirfleetManufacturer'
    __table_args__ = (
        PrimaryKeyConstraint('airfleet_manufacturer_id', name='PK__AirfeetM__C8F84F029B7AD205'),
    )

    airfleet_manufacturer_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    airfleet_manufacturer_name: Mapped[Optional[str]] = mapped_column(String(20, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    Airfleet: Mapped[list[Airfleet]] = relationship('Airfleet', back_populates='airfleet_manufacturer')


class Airfleet(Base):
    __tablename__ = 'Airfleet'
    __table_args__ = (
        ForeignKeyConstraint(['airfleet_manufacturer_id'], ['AirfleetManufacturer.airfleet_manufacturer_id'], name='FK_Airfeet_AirfeetManufacturer'),
        PrimaryKeyConstraint('airfleet_id', name='PK__Airfleet__E537D89C85F2878A'),
    )

    airfleet_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    airfleet_manufacturer_id: Mapped[Optional[int]] = mapped_column(Integer)
    aircraft_range_km: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(7, 2))
    aircraft_model: Mapped[Optional[str]] = mapped_column(String(25, 'SQL_Latin1_General_CP1_CI_AS'))
    aircraft_speed: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(7, 2))
    seat_capacity: Mapped[Optional[int]] = mapped_column(Integer)
    baggage_capacity: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(8, 2))
    aircraft_fuel_consumption: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(8, 2))
    aircraft_performance: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(15, 4), Computed('([aircraft_speed]*[aircraft_range_km])', persisted=True))
    aircraft_url: Mapped[Optional[str]] = mapped_column(Unicode(255, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    airfleet_manufacturer: Mapped[Optional[AirfleetManufacturer]] = relationship('AirfleetManufacturer', back_populates='Airfleet')
    AirlineAirfleet: Mapped[list[AirlineAirfleet]] = relationship('AirlineAirfleet', back_populates='airfleet')
    SeatLayout: Mapped[list[SeatLayout]] = relationship('SeatLayout', back_populates='airfleet')
    AirfleetFlightCrew: Mapped[list[AirfleetFlightCrew]] = relationship('AirfleetFlightCrew', back_populates='airfleet')
    Flight: Mapped[list[Flight]] = relationship('Flight', back_populates='airfleet')
    FlightOperation: Mapped[list[FlightOperation]] = relationship('FlightOperation', back_populates='airfleet')


class AirfleetFlightCrew(Base):
    __tablename__ = 'AirfleetFlightCrew'
    __table_args__ = (
        ForeignKeyConstraint(['airfleet_id'], ['Airfleet.airfleet_id'], name='FK_AirfleetFlightCrew_Airfleet'),
        ForeignKeyConstraint(['flight_crew_id'], ['FlightCrew.flight_crew_id'], name='FK_AirfleetFlightCrew_FlightCrew'),
        PrimaryKeyConstraint('airfleet_id', 'flight_crew_id', name='PK__Airfleet__E72ECAE04C8D85C5'),
    )

    airfleet_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_crew_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    airfleet: Mapped[Airfleet] = relationship('Airfleet', back_populates='AirfleetFlightCrew')
    flight_crew: Mapped[FlightCrew] = relationship('FlightCrew', back_populates='AirfleetFlightCrew')