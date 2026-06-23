from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .airport_model import Country
    from .airfleet_model import Airfleet
    from .crew_model import FlightCrew
    from .flight_model import Flight

from sqlalchemy import ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Unicode, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Alliance(Base):
    __tablename__ = 'Alliance'
    __table_args__ = (
        PrimaryKeyConstraint('airline_alliance_id', name='PK_Alliance'),
    )

    airline_alliance_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    alliance_name: Mapped[str] = mapped_column(String(20, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    alliance_founded_year: Mapped[int] = mapped_column(Integer, nullable=False)

    Airline: Mapped[list[Airline]] = relationship('Airline', back_populates='alliance')


class Airline(Base):
    __tablename__ = 'Airline'
    __table_args__ = (
        ForeignKeyConstraint(['alliance_id'], ['Alliance.airline_alliance_id'], name='FK_Airline_Alliance'),
        ForeignKeyConstraint(['country_id'], ['Country.country_id'], name='FK_Airline_Country'),
        PrimaryKeyConstraint('airline_id', name='PK__Airline__A016BF806CAA5507'),
        Index('UQ_Airline_iata_code', 'iata_code', mssql_clustered=False, unique=True),
    )

    airline_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    iata_code: Mapped[str] = mapped_column(String(2, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    country_id: Mapped[Optional[int]] = mapped_column(Integer)
    airline_name: Mapped[Optional[str]] = mapped_column(String(35, 'SQL_Latin1_General_CP1_CI_AS'))
    airline_url: Mapped[Optional[str]] = mapped_column(Unicode(255, 'SQL_Latin1_General_CP1_CI_AS'))
    alliance_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    alliance: Mapped[Optional[Alliance]] = relationship('Alliance', back_populates='Airline')
    country: Mapped[Optional[Country]] = relationship('Country', back_populates='Airline')
    AirlineAirfleet: Mapped[list[AirlineAirfleet]] = relationship('AirlineAirfleet', back_populates='airline')
    FlightCrew: Mapped[list[FlightCrew]] = relationship('FlightCrew', back_populates='airline')
    Flight: Mapped[list[Flight]] = relationship('Flight', back_populates='airline')


class AirlineAirfleet(Base):
    __tablename__ = 'AirlineAirfleet'
    __table_args__ = (
        ForeignKeyConstraint(['airfleet_id'], ['Airfleet.airfleet_id'], name='FK_Airfleet'),
        ForeignKeyConstraint(['airline_id'], ['Airline.airline_id'], name='FK_Airline'),
        PrimaryKeyConstraint('airline_id', 'airfleet_id', name='PK_Airline_Airfleet'),
    )

    airline_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airfleet_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    airfleet: Mapped[Airfleet] = relationship('Airfleet', back_populates='AirlineAirfleet')
    airline: Mapped[Airline] = relationship('Airline', back_populates='AirlineAirfleet')