from __future__ import annotations
import datetime
import decimal
from typing import Optional

from sqlalchemy import DECIMAL, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Country(Base):
    __tablename__ = 'Country'
    __table_args__ = (
        PrimaryKeyConstraint('country_id', name='PK__Country__7E8CD055A31DB915'),
    )

    country_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    country_name: Mapped[Optional[str]] = mapped_column(String(20, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    Airline: Mapped[list['Airline']] = relationship('Airline', back_populates='country')
    City: Mapped[list['City']] = relationship('City', back_populates='country')


class City(Base):
    __tablename__ = 'City'
    __table_args__ = (
        ForeignKeyConstraint(['country_id'], ['Country.country_id'], name='FK_City_Country'),
        PrimaryKeyConstraint('city_id', name='PK__City__031491A8E75E20C9'),
    )

    city_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    country_id: Mapped[Optional[int]] = mapped_column(Integer)
    city_name: Mapped[Optional[str]] = mapped_column(String(50, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    country: Mapped[Optional['Country']] = relationship('Country', back_populates='City')
    Airport: Mapped[list['Airport']] = relationship('Airport', back_populates='city')


class Airport(Base):
    __tablename__ = 'Airport'
    __table_args__ = (
        ForeignKeyConstraint(['city_id'], ['City.city_id'], name='FK_Airport_City'),
        PrimaryKeyConstraint('airport_id', name='PK__Airport__C795D5166E212F4B'),
        Index('UQ_Airport_airport_code', 'airport_code', mssql_clustered=False, unique=True),
    )

    airport_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    city_id: Mapped[Optional[int]] = mapped_column(Integer)
    airport_name: Mapped[Optional[str]] = mapped_column(String(100, 'SQL_Latin1_General_CP1_CI_AS'))
    airport_address: Mapped[Optional[str]] = mapped_column(String(200, 'SQL_Latin1_General_CP1_CI_AS'))
    airport_code: Mapped[Optional[str]] = mapped_column(String(5, 'SQL_Latin1_General_CP1_CI_AS'))
    latitude: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(9, 6))
    longitude: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(9, 6))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    city: Mapped[Optional['City']] = relationship('City', back_populates='Airport')
    CheckInAgent: Mapped[list['CheckInAgent']] = relationship('CheckInAgent', back_populates='airport')
    Route_arrives_airport: Mapped[list['Route']] = relationship('Route', foreign_keys='[Route.arrives_airport_id]', back_populates='arrives_airport')
    Route_departs_airport: Mapped[list['Route']] = relationship('Route', foreign_keys='[Route.departs_airport_id]', back_populates='departs_airport')
    Terminal: Mapped[list['Terminal']] = relationship('Terminal', back_populates='airport')


class TerminalType(Base):
    __tablename__ = 'TerminalType'
    __table_args__ = (
        PrimaryKeyConstraint('terminal_type_id', name='PK__Terminal__8D3FF2716CB6171E'),
    )

    terminal_type_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    terminal_type_name: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    Terminal: Mapped[list['Terminal']] = relationship('Terminal', back_populates='terminal_type')


class Terminal(Base):
    __tablename__ = 'Terminal'
    __table_args__ = (
        ForeignKeyConstraint(['airport_id'], ['Airport.airport_id'], name='FKTerminal_Airport'),
        ForeignKeyConstraint(['terminal_type_id'], ['TerminalType.terminal_type_id'], name='FKTerminal_TerminalType'),
        PrimaryKeyConstraint('terminal_id', name='PK__Terminal__A7A7EB41F5C7199B'),
        Index('UQ_Terminal_airport_code', 'airport_id', 'terminal_code', mssql_clustered=False, unique=True),
    )

    terminal_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    airport_id: Mapped[int] = mapped_column(Integer, nullable=False)
    terminal_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    terminal_code: Mapped[str] = mapped_column(String(4, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    terminal_size: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    airport: Mapped['Airport'] = relationship('Airport', back_populates='Terminal')
    terminal_type: Mapped['TerminalType'] = relationship('TerminalType', back_populates='Terminal')
    Gate: Mapped[list['Gate']] = relationship('Gate', back_populates='terminal')


class Gate(Base):
    __tablename__ = 'Gate'
    __table_args__ = (
        ForeignKeyConstraint(['terminal_id'], ['Terminal.terminal_id'], name='FK_Gate_Terminal'),
        PrimaryKeyConstraint('gate_id', name='PK__Gate__8CB11922B469D3FB'),
        Index('UQ_Gate_TerminalGate', 'terminal_id', 'gate_code', mssql_clustered=False, unique=True),
    )

    gate_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    terminal_id: Mapped[int] = mapped_column(Integer, nullable=False)
    gate_code: Mapped[str] = mapped_column(String(5, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    terminal: Mapped['Terminal'] = relationship('Terminal', back_populates='Gate')
    FlightOperation: Mapped[list['FlightOperation']] = relationship('FlightOperation', back_populates='gate')