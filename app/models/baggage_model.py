from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from .base import Base


class BaggageType(Base):
    __tablename__ = "BaggageType"

    baggage_type_id   = Column(Integer, primary_key=True)
    baggage_type_name = Column(String)


class BaggagePricingRule(Base):
    __tablename__ = "BaggagePricingRule"

    baggage_pricing_rule_id = Column(Integer, primary_key=True)
    baggage_type_id         = Column(Integer, ForeignKey("BaggageType.baggage_type_id"))
    baggage_dimension       = Column(String)
    baggage_max_weight      = Column(DECIMAL(5, 2))
    overweight_fee_per_kg   = Column(DECIMAL(6, 2))

    baggage_type = relationship("BaggageType")


class BaggagePricingInFlight(Base):
    __tablename__ = "BaggagePricingInFlight"

    baggage_pricing_in_flight_id = Column(Integer, primary_key=True)
    flight_id                    = Column(Integer, ForeignKey("Flight.flight_id"))
    baggage_pricing_rule_id      = Column(Integer, ForeignKey("BaggagePricingRule.baggage_pricing_rule_id"))
    flight_class_id              = Column(Integer, ForeignKey("FlightClass.flight_class_id"))
    baggage_price                = Column(DECIMAL(7, 2))

    baggage_pricing_rule = relationship("BaggagePricingRule")


class BaggageOptionInFlight(Base):
    __tablename__ = "BaggageOptionInFlight"

    baggage_option_in_flight_id  = Column(Integer, primary_key=True)
    baggage_pricing_in_flight_id = Column(Integer, ForeignKey("BaggagePricingInFlight.baggage_pricing_in_flight_id"))
    booking_item_id              = Column(Integer, ForeignKey("BookingItem.booking_item_id"), unique=True)
    baggage_quantity             = Column(Integer)

    baggage_pricing_in_flight = relationship("BaggagePricingInFlight")