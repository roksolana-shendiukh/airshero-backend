from __future__ import annotations
import datetime
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Citizenship(Base):
    __tablename__ = 'Citizenship'
    __table_args__ = (
        PrimaryKeyConstraint('citizenship_id', name='PK__Citizens__4AB65D725ADB713D'),
    )

    citizenship_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    citizenship_name: Mapped[Optional[str]] = mapped_column(String(20, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    PassengerDocument: Mapped[list['PassengerDocument']] = relationship('PassengerDocument', back_populates='citizenship')


class DocumentType(Base):
    __tablename__ = 'DocumentType'
    __table_args__ = (
        PrimaryKeyConstraint('document_type_id', name='PK__Document__69F7C2B1FB6F8851'),
    )

    document_type_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    document_type_name: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    document_type_code: Mapped[Optional[str]] = mapped_column(String(10, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    PassengerDocument: Mapped[list['PassengerDocument']] = relationship('PassengerDocument', back_populates='document_type')


class Passenger(Base):
    __tablename__ = 'Passenger'
    __table_args__ = (
        PrimaryKeyConstraint('passenger_id', name='PK__Passenge__0376458610BC5B67'),
        Index('IX_Passenger_LastName_Sex', 'passenger_last_name', 'passenger_sex', mssql_clustered=False),
    )

    passenger_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    passenger_first_name: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    passenger_last_name: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    passenger_sex: Mapped[Optional[bool]] = mapped_column(Boolean)
    passenger_email: Mapped[Optional[str]] = mapped_column(String(45, 'SQL_Latin1_General_CP1_CI_AS'))
    passenger_date_of_birth: Mapped[Optional[datetime.date]] = mapped_column(Date)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    PassengerDocument: Mapped[list['PassengerDocument']] = relationship('PassengerDocument', back_populates='passenger')


class PassengerDocument(Base):
    __tablename__ = 'PassengerDocument'
    __table_args__ = (
        ForeignKeyConstraint(['citizenship_id'], ['Citizenship.citizenship_id'], name='FK_PassengerDocument_Citizenship'),
        ForeignKeyConstraint(['document_type_id'], ['DocumentType.document_type_id'], name='FK_PassengerDocument_DocumentType'),
        ForeignKeyConstraint(['passenger_id'], ['Passenger.passenger_id'], name='FK_PassengerDocument_Passenger'),
        PrimaryKeyConstraint('passenger_document_id', name='PK__Passenge__553972D27ED62B3F'),
        Index('IX_PassengerDocument_PassengerId', 'passenger_id', mssql_clustered=False),
        Index('UQ_PassengerDocument_document_number', 'document_number', mssql_clustered=False, unique=True),
    )

    passenger_document_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    passenger_id: Mapped[Optional[int]] = mapped_column(Integer)
    citizenship_id: Mapped[Optional[int]] = mapped_column(Integer)
    document_type_id: Mapped[Optional[int]] = mapped_column(Integer)
    document_number: Mapped[Optional[str]] = mapped_column(String(10, 'SQL_Latin1_General_CP1_CI_AS'))
    document_date_of_issue: Mapped[Optional[datetime.date]] = mapped_column(Date)
    document_date_of_expire: Mapped[Optional[datetime.date]] = mapped_column(Date)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(sysutcdatetime())'))

    citizenship: Mapped[Optional['Citizenship']] = relationship('Citizenship', back_populates='PassengerDocument')
    document_type: Mapped[Optional['DocumentType']] = relationship('DocumentType', back_populates='PassengerDocument')
    passenger: Mapped[Optional['Passenger']] = relationship('Passenger', back_populates='PassengerDocument')
    BookingItem: Mapped[list['BookingItem']] = relationship('BookingItem', back_populates='passenger_document')