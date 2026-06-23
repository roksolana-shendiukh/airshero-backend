import datetime
import decimal
from typing import Optional

from sqlalchemy import Column, DECIMAL, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Table, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class BaggageType(Base):
    __tablename__ = 'BaggageType'
    __table_args__ = (
        PrimaryKeyConstraint('baggage_type_id', name='PK__BaggageT__EA687A60235828D7'),
    )

    baggage_type_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    baggage_type_name: Mapped[Optional[str]] = mapped_column(String(20, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    BaggagePricingRule: Mapped[list['BaggagePricingRule']] = relationship('BaggagePricingRule', back_populates='baggage_type')
    BaggageUnit: Mapped[list['BaggageUnit']] = relationship('BaggageUnit', back_populates='baggage_type')


class BaggagePricingRule(Base):
    __tablename__ = 'BaggagePricingRule'
    __table_args__ = (
        ForeignKeyConstraint(['baggage_type_id'], ['BaggageType.baggage_type_id'], name='FK_BaggagePricingRule_BaggageType'),
        PrimaryKeyConstraint('baggage_pricing_rule_id', name='PK__BaggageP__9E0A031F6ADB3BFB'),
    )

    baggage_pricing_rule_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    baggage_type_id: Mapped[Optional[int]] = mapped_column(Integer)
    baggage_dimension: Mapped[Optional[str]] = mapped_column(String(15, 'SQL_Latin1_General_CP1_CI_AS'))
    baggage_max_weight: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(5, 2))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    baggage_type: Mapped[Optional['BaggageType']] = relationship('BaggageType', back_populates='BaggagePricingRule')
    BaggagePricingInFlight: Mapped[list['BaggagePricingInFlight']] = relationship('BaggagePricingInFlight', back_populates='baggage_pricing_rule')


class BaggagePricingInFlight(Base):
    __tablename__ = 'BaggagePricingInFlight'
    __table_args__ = (
        ForeignKeyConstraint(['baggage_pricing_rule_id'], ['BaggagePricingRule.baggage_pricing_rule_id'], name='FK_BaggagePricingInFlight_BaggagePricingRule'),
        ForeignKeyConstraint(['flight_class_id'], ['FlightClass.flight_class_id'], name='FK_BaggagePricingInFlight_FlightClass'),
        PrimaryKeyConstraint('baggage_pricing_in_flight_id', name='PK__BaggageP__091282990910598B'),
    )

    baggage_pricing_in_flight_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    baggage_pricing_rule_id: Mapped[Optional[int]] = mapped_column(Integer)
    flight_class_id: Mapped[Optional[int]] = mapped_column(Integer)
    baggage_price: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(7, 2))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    baggage_pricing_rule: Mapped[Optional['BaggagePricingRule']] = relationship('BaggagePricingRule', back_populates='BaggagePricingInFlight')
    flight_class: Mapped[Optional['FlightClass']] = relationship('FlightClass', back_populates='BaggagePricingInFlight')
    BaggageOptionInFlight: Mapped[list['BaggageOptionInFlight']] = relationship('BaggageOptionInFlight', back_populates='baggage_pricing_in_flight')


class BaggageOptionInFlight(Base):
    __tablename__ = 'BaggageOptionInFlight'
    __table_args__ = (
        ForeignKeyConstraint(['baggage_pricing_in_flight_id'], ['BaggagePricingInFlight.baggage_pricing_in_flight_id'], name='FK_BaggageOptionInFlight_BaggagePricingInFlight'),
        ForeignKeyConstraint(['booking_item_id'], ['BookingItem.booking_item_id'], name='FK_BaggageOptionInFlight_BookingItem'),
        PrimaryKeyConstraint('baggage_option_in_flight_id', name='PK__BaggageO__045DBCF6E84CEA5F'),
        Index('IX_BaggageOption_BookingItem_Rule', 'booking_item_id', 'baggage_pricing_in_flight_id', mssql_clustered=False, mssql_include=['baggage_quantity']),
    )

    baggage_option_in_flight_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    baggage_pricing_in_flight_id: Mapped[Optional[int]] = mapped_column(Integer)
    booking_item_id: Mapped[Optional[int]] = mapped_column(Integer)
    baggage_quantity: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    baggage_pricing_in_flight: Mapped[Optional['BaggagePricingInFlight']] = relationship('BaggagePricingInFlight', back_populates='BaggageOptionInFlight')
    booking_item: Mapped[Optional['BookingItem']] = relationship('BookingItem', back_populates='BaggageOptionInFlight')


class BaggageUnit(Base):
    __tablename__ = 'BaggageUnit'
    __table_args__ = (
        ForeignKeyConstraint(['baggage_type_id'], ['BaggageType.baggage_type_id'], name='FKBaggageUnit_BaggageType'),
        ForeignKeyConstraint(['boarding_pass_id'], ['BoardingPass.boarding_pass_id'], name='FKBaggageUnit_BoardingPass'),
        PrimaryKeyConstraint('baggage_unit_id', name='PK__BaggageU__0480A76C3FF3EC9A'),
        Index('UQ__BaggageU__FD7461E38C53DED8', 'baggage_unit_tracking_number', mssql_clustered=False, unique=True),
    )

    baggage_unit_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    baggage_unit_tracking_number: Mapped[str] = mapped_column(String(12, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    boarding_pass_id: Mapped[Optional[int]] = mapped_column(Integer)
    baggage_type_id: Mapped[Optional[int]] = mapped_column(Integer)
    baggage_unit_weight_kg: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(5, 2))
    baggage_unit_dimensions: Mapped[Optional[str]] = mapped_column(String(10, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    baggage_type: Mapped[Optional['BaggageType']] = relationship('BaggageType', back_populates='BaggageUnit')
    boarding_pass: Mapped[Optional['BoardingPass']] = relationship('BoardingPass', back_populates='BaggageUnit')


t_BaggageUnitCheckInPayment = Table(
    'BaggageUnitCheckInPayment', Base.metadata,
    Column('baggage_unit_id', Integer, nullable=False),
    Column('checkin_payment_id', Integer, nullable=False),
    Column('created_at', DATETIME2, server_default=text('(getdate())')),
    Column('updated_at', DATETIME2),
    ForeignKeyConstraint(['baggage_unit_id'], ['BaggageUnit.baggage_unit_id'], name='FKBaggageUnit'),
    ForeignKeyConstraint(['checkin_payment_id'], ['CheckinInPayment.checkin_payment_id'], name='FKCheckinInPayment'),
)