from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .flight_model import Flight

from sqlalchemy import Date, ForeignKeyConstraint, Identity, Integer, PrimaryKeyConstraint, String, Time, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class FlightSeason(Base):
    __tablename__ = 'FlightSeason'
    __table_args__ = (
        PrimaryKeyConstraint('flight_season_id', name='PK_FlightSeason'),
    )

    flight_season_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    season_start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    season_end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    FlightSchedule: Mapped[list[FlightSchedule]] = relationship('FlightSchedule', back_populates='flight_season')


class Schedule(Base):
    __tablename__ = 'Schedule'
    __table_args__ = (
        PrimaryKeyConstraint('schedule_id', name='PK__Schedule__C46A8A6F6E1B353B'),
    )

    schedule_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    schedule_arrival_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    schedule_departure_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    DaySchedule: Mapped[list[DaySchedule]] = relationship('DaySchedule', back_populates='schedule')


class DayForSchedule(Base):
    __tablename__ = 'DayForSchedule'
    __table_args__ = (
        PrimaryKeyConstraint('day_id', name='PK__DayForSc__8B516ABBA4663310'),
    )

    day_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    day_name: Mapped[Optional[str]] = mapped_column(String(10, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    DaySchedule: Mapped[list[DaySchedule]] = relationship('DaySchedule', back_populates='day')


class DaySchedule(Base):
    __tablename__ = 'DaySchedule'
    __table_args__ = (
        ForeignKeyConstraint(['day_id'], ['DayForSchedule.day_id'], name='FK_DaySchedule_Day'),
        ForeignKeyConstraint(['schedule_id'], ['Schedule.schedule_id'], name='FK_DaySchedule_Schedule'),
        PrimaryKeyConstraint('day_schedule_id', name='PK__DaySched__BC44FB659FBC70D1'),
    )

    day_schedule_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    schedule_id: Mapped[Optional[int]] = mapped_column(Integer)
    day_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    day: Mapped[Optional[DayForSchedule]] = relationship('DayForSchedule', back_populates='DaySchedule')
    schedule: Mapped[Optional[Schedule]] = relationship('Schedule', back_populates='DaySchedule')
    FlightScheduleDaySchedule: Mapped[list[FlightScheduleDaySchedule]] = relationship('FlightScheduleDaySchedule', back_populates='day_schedule')


class FlightSchedule(Base):
    __tablename__ = 'FlightSchedule'
    __table_args__ = (
        ForeignKeyConstraint(['flight_id'], ['Flight.flight_id'], name='FK_FlightSchedule_Flight'),
        ForeignKeyConstraint(['flight_season_id'], ['FlightSeason.flight_season_id'], name='FK_FlightSchedule_FlightSeason'),
        PrimaryKeyConstraint('flight_schedule_id', name='PK__FlightSc__01C9F54D6E22B7D0'),
    )

    flight_schedule_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    flight_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('((0))'))
    flight_season_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('((0))'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    flight: Mapped[Flight] = relationship('Flight', back_populates='FlightSchedule')
    flight_season: Mapped[FlightSeason] = relationship('FlightSeason', back_populates='FlightSchedule')
    FlightScheduleDaySchedule: Mapped[list[FlightScheduleDaySchedule]] = relationship('FlightScheduleDaySchedule', back_populates='flight_schedule')


class FlightScheduleDaySchedule(Base):
    __tablename__ = 'FlightScheduleDaySchedule'
    __table_args__ = (
        ForeignKeyConstraint(['day_schedule_id'], ['DaySchedule.day_schedule_id'], name='FK_DaySchedule'),
        ForeignKeyConstraint(['flight_schedule_id'], ['FlightSchedule.flight_schedule_id'], name='FK_FlightSchedule'),
        PrimaryKeyConstraint('flight_schedule_id', 'day_schedule_id', name='PK_FlightSchedule_DaySchedule'),
    )

    flight_schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    day_schedule: Mapped[DaySchedule] = relationship('DaySchedule', back_populates='FlightScheduleDaySchedule')
    flight_schedule: Mapped[FlightSchedule] = relationship('FlightSchedule', back_populates='FlightScheduleDaySchedule')
