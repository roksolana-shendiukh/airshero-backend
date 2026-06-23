from __future__ import annotations
import datetime
import decimal
from typing import Optional

from sqlalchemy import DECIMAL, DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PaymentMethod(Base):
    __tablename__ = 'PaymentMethod'
    __table_args__ = (
        PrimaryKeyConstraint('payment_method_id', name='PK__PaymentM__8A3EA9EB966E06D9'),
    )

    payment_method_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    payment_method_name: Mapped[Optional[str]] = mapped_column(String(20, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    CheckinInPayment: Mapped[list['CheckinInPayment']] = relationship('CheckinInPayment', back_populates='payment_method')
    Payment: Mapped[list['Payment']] = relationship('Payment', back_populates='payment_method')


class PaymentStatus(Base):
    __tablename__ = 'PaymentStatus'
    __table_args__ = (
        PrimaryKeyConstraint('payment_status_id', name='PK__PaymentS__E6BF5015C832A6D3'),
    )

    payment_status_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    payment_status_name: Mapped[Optional[str]] = mapped_column(String(18, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    CheckinInPayment: Mapped[list['CheckinInPayment']] = relationship('CheckinInPayment', back_populates='payment_status')
    Payment: Mapped[list['Payment']] = relationship('Payment', back_populates='payment_status')


class Payment(Base):
    __tablename__ = 'Payment'
    __table_args__ = (
        ForeignKeyConstraint(['booking_id'], ['Booking.booking_id'], name='FK_Payment_Booking'),
        ForeignKeyConstraint(['payment_method_id'], ['PaymentMethod.payment_method_id'], name='FK_Payment_PaymentMethod'),
        ForeignKeyConstraint(['payment_status_id'], ['PaymentStatus.payment_status_id'], name='FK_Payment_PaymentStatus'),
        PrimaryKeyConstraint('payment_id', name='PK__Payment__ED1FC9EAD2DE10B9'),
        Index('IX_Payment_BookingId', 'booking_id', mssql_clustered=False),
    )

    payment_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    booking_id: Mapped[Optional[int]] = mapped_column(Integer)
    payment_status_id: Mapped[Optional[int]] = mapped_column(Integer)
    payment_method_id: Mapped[Optional[int]] = mapped_column(Integer)
    payment_date_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    payment_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    booking: Mapped[Optional['Booking']] = relationship('Booking', back_populates='Payment')
    payment_method: Mapped[Optional['PaymentMethod']] = relationship('PaymentMethod', back_populates='Payment')
    payment_status: Mapped[Optional['PaymentStatus']] = relationship('PaymentStatus', back_populates='Payment')


class CheckinInPayment(Base):
    __tablename__ = 'CheckinInPayment'
    __table_args__ = (
        ForeignKeyConstraint(['payment_method_id'], ['PaymentMethod.payment_method_id'], name='FKCheckinInPayment_PaymentMethod'),
        ForeignKeyConstraint(['payment_status_id'], ['PaymentStatus.payment_status_id'], name='FKCheckinInPayment_PaymentStatus'),
        PrimaryKeyConstraint('checkin_payment_id', name='PK__CheckinI__3AAEC0E542C454E0'),
    )

    checkin_payment_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    payment_status_id: Mapped[Optional[int]] = mapped_column(Integer)
    payment_method_id: Mapped[Optional[int]] = mapped_column(Integer)
    checkin_payment_date_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    checkin_payment_amount: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(8, 2))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    payment_method: Mapped[Optional['PaymentMethod']] = relationship('PaymentMethod', back_populates='CheckinInPayment')
    payment_status: Mapped[Optional['PaymentStatus']] = relationship('PaymentStatus', back_populates='CheckinInPayment')