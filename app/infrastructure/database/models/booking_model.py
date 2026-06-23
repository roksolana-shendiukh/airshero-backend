from __future__ import annotations
import datetime
import decimal
from typing import Optional

from sqlalchemy import DECIMAL, DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class BookingStatus(Base):
    __tablename__ = 'BookingStatus'
    __table_args__ = (
        PrimaryKeyConstraint('booking_status_id', name='PK__BookingS__B02F4E9E0CCDF8EA'),
    )

    booking_status_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    booking_status_name: Mapped[Optional[str]] = mapped_column(String(15, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    Booking: Mapped[list['Booking']] = relationship('Booking', back_populates='booking_status')


class Booking(Base):
    __tablename__ = 'Booking'
    __table_args__ = (
        ForeignKeyConstraint(['booking_status_id'], ['BookingStatus.booking_status_id'], name='FK_Booking_BookingStatus'),
        PrimaryKeyConstraint('booking_id', name='PK__Booking__5DE3A5B1EDAADC51'),
        Index('IX_Booking_Status_Date', 'booking_status_id', 'booking_date_time', mssql_clustered=False),
        Index('UQ__Booking__3A30D2BC8195861E', 'booking_number', mssql_clustered=False, unique=True),
    )

    booking_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    booking_status_id: Mapped[int] = mapped_column(Integer, nullable=False)
    booking_number: Mapped[str] = mapped_column(String(10, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    booking_date_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    booking_total_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    booking_status: Mapped['BookingStatus'] = relationship('BookingStatus', back_populates='Booking')
    Payment: Mapped[list['Payment']] = relationship('Payment', back_populates='booking')
    BookingItem: Mapped[list['BookingItem']] = relationship('BookingItem', back_populates='booking')


class BookingItem(Base):
    __tablename__ = 'BookingItem'
    __table_args__ = (
        ForeignKeyConstraint(['booking_id'], ['Booking.booking_id'], name='FK_BookingItem_Booking'),
        ForeignKeyConstraint(['flight_price_id'], ['FlightPrice.flight_price_id'], name='FK_BookingItem_FlightPrice'),
        ForeignKeyConstraint(['passenger_document_id'], ['PassengerDocument.passenger_document_id'], name='FK_BookingItem_PassengerDocument'),
        PrimaryKeyConstraint('booking_item_id', name='PK__BookingI__E577F61C69F4A391'),
        Index('IX_BookingItem_BookingId', 'booking_id', mssql_clustered=False),
        Index('IX_BookingItem_PassengerDocumentId', 'passenger_document_id', mssql_clustered=False),
    )

    booking_item_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    passenger_document_id: Mapped[Optional[int]] = mapped_column(Integer)
    booking_id: Mapped[Optional[int]] = mapped_column(Integer)
    flight_price_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    booking: Mapped[Optional['Booking']] = relationship('Booking', back_populates='BookingItem')
    flight_price: Mapped[Optional['FlightPrice']] = relationship('FlightPrice', back_populates='BookingItem')
    passenger_document: Mapped[Optional['PassengerDocument']] = relationship('PassengerDocument', back_populates='BookingItem')
    BaggageOptionInFlight: Mapped[list['BaggageOptionInFlight']] = relationship('BaggageOptionInFlight', back_populates='booking_item')