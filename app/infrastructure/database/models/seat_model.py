import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .airfleet_model import Airfleet
    from .flight_model import FlightClass


class Class(Base):
    __tablename__ = 'Class'
    __table_args__ = (
        PrimaryKeyConstraint('class_id', name='PK__Class__FDF4798698ACACB5'),
    )

    class_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    class_name: Mapped[Optional[str]] = mapped_column(String(15, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    SeatLayout: Mapped[list['SeatLayout']] = relationship('SeatLayout', back_populates='class_')
    FlightClass: Mapped[list['FlightClass']] = relationship('FlightClass', back_populates='class_')


class SeatType(Base):
    __tablename__ = 'SeatType'
    __table_args__ = (
        PrimaryKeyConstraint('seat_type_id', name='PK__SeatType__906DED9C56D6DB54'),
    )

    seat_type_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    seat_type_name: Mapped[Optional[str]] = mapped_column(String(20, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    SeatLayout: Mapped[list['SeatLayout']] = relationship('SeatLayout', back_populates='seat_type')


class SeatLayout(Base):
    __tablename__ = 'SeatLayout'
    __table_args__ = (
        ForeignKeyConstraint(['airfleet_id'], ['Airfleet.airfleet_id'], name='FK_SeatLayout_Airfleet'),
        ForeignKeyConstraint(['class_id'], ['Class.class_id'], name='FK_SeatLayout_Class'),
        ForeignKeyConstraint(['seat_type_id'], ['SeatType.seat_type_id'], name='FKSeatLayout_SeatType'),
        PrimaryKeyConstraint('seat_layout_id', name='PK__SeatLayo__20F8C0CE7A306F1E'),
        Index('UQ_SeatLayout_Composite', 'airfleet_id', 'seat_layout_rows', 'seat_layout_columns', mssql_clustered=False, unique=True),
    )

    seat_layout_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    seat_type_id: Mapped[Optional[int]] = mapped_column(Integer)
    class_id: Mapped[Optional[int]] = mapped_column(Integer)
    airfleet_id: Mapped[Optional[int]] = mapped_column(Integer)
    seat_layout_rows: Mapped[Optional[int]] = mapped_column(Integer)
    seat_layout_columns: Mapped[Optional[str]] = mapped_column(String(3, 'SQL_Latin1_General_CP1_CI_AS'))
    is_emergency_exit: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('((0))'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    airfleet: Mapped[Optional['Airfleet']] = relationship('Airfleet', back_populates='SeatLayout')
    class_: Mapped[Optional['Class']] = relationship('Class', back_populates='SeatLayout')
    seat_type: Mapped[Optional['SeatType']] = relationship('SeatType', back_populates='SeatLayout')