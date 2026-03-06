from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL, Time, Date
from sqlalchemy.orm import relationship
from .base import Base


class FlightStatus(Base):
    __tablename__ = "FlightStatus"

    flight_status_id = Column(Integer, primary_key=True)
    flight_status_name = Column(String)


class Airline(Base):
    __tablename__ = "Airline"

    airline_id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("Country.country_id"))
    airline_name = Column(String)
    iata_code = Column(String, unique=True)
    airline_url = Column(String)


class Airport(Base):
    __tablename__ = "Airport"

    airport_id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("City.city_id"))
    airport_name = Column(String)
    airport_address = Column(String)
    airport_code = Column(String, unique=True)


class Route(Base):
    __tablename__ = "Route"

    route_id = Column(Integer, primary_key=True)
    airline_id = Column(Integer, ForeignKey("Airline.airline_id"))
    airfleet_id = Column(Integer, ForeignKey("Airfleet.airfleet_id"))
    departs_airport_id = Column(Integer, ForeignKey("Airport.airport_id"))
    arrives_airport_id = Column(Integer, ForeignKey("Airport.airport_id"))
    flight_number = Column(String, unique=True)
    flight_range = Column(DECIMAL(7, 2))
    flight_duration = Column(Time)

    airline = relationship("Airline")
    departs_airport = relationship("Airport", foreign_keys=[departs_airport_id])
    arrives_airport = relationship("Airport", foreign_keys=[arrives_airport_id])


class FlightSchedule(Base):
    __tablename__ = "FlightSchedule"

    flight_schedule_id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey("Route.route_id"))
    flight_start_date = Column(Date)
    flight_end_date = Column(Date)

    route = relationship("Route")


class Flight(Base):
    __tablename__ = "Flight"

    flight_id = Column(Integer, primary_key=True)
    flight_status_id = Column(Integer, ForeignKey("FlightStatus.flight_status_id"))
    flight_schedule_id = Column(Integer, ForeignKey("FlightSchedule.flight_schedule_id"))
    departs_datetime = Column(DateTime)
    arrives_datetime = Column(DateTime)

    flight_status = relationship("FlightStatus")
    flight_schedule = relationship("FlightSchedule")
    flight_classes = relationship("FlightClass", back_populates="flight")


class Class(Base):
    __tablename__ = "Class"

    class_id = Column(Integer, primary_key=True)
    class_name = Column(String)


class FlightClass(Base):
    __tablename__ = "FlightClass"

    flight_class_id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("Class.class_id"))
    flight_id = Column(Integer, ForeignKey("Flight.flight_id"))

    flight = relationship("Flight", back_populates="flight_classes")
    cls = relationship("Class")
    prices = relationship("FlightPrice", back_populates="flight_class")


class FlightPrice(Base):
    __tablename__ = "FlightPrice"

    flight_price_id = Column(Integer, primary_key=True)
    flight_class_id = Column(Integer, ForeignKey("FlightClass.flight_class_id"))
    flight_published_date = Column(Date)
    ticket_price = Column(DECIMAL(8, 2))

    flight_class = relationship("FlightClass", back_populates="prices")


class BaggageType(Base):
    __tablename__ = "BaggageType"

    baggage_type_id = Column(Integer, primary_key=True)
    baggage_type_name = Column(String)


class BaggagePricingRule(Base):
    __tablename__ = "BaggagePricingRule"

    baggage_pricing_rule_id = Column(Integer, primary_key=True)
    baggage_type_id = Column(Integer, ForeignKey("BaggageType.baggage_type_id"))
    baggage_dimension = Column(String)
    baggage_max_weight = Column(DECIMAL(5, 2))
    overweight_fee_per_kg = Column(DECIMAL(6, 2))

    baggage_type = relationship("BaggageType")


class BaggagePricingInFlight(Base):
    __tablename__ = "BaggagePricingInFlight"

    baggage_pricing_in_flight_id = Column(Integer, primary_key=True)
    flight_id = Column(Integer, ForeignKey("Flight.flight_id"))
    baggage_pricing_rule_id = Column(Integer, ForeignKey("BaggagePricingRule.baggage_pricing_rule_id"))
    flight_class_id = Column(Integer, ForeignKey("FlightClass.flight_class_id"))
    baggage_price = Column(DECIMAL(7, 2))

    baggage_pricing_rule = relationship("BaggagePricingRule")


class BaggageOptionInFlight(Base):
    __tablename__ = "BaggageOptionInFlight"

    baggage_option_in_flight_id = Column(Integer, primary_key=True)
    baggage_pricing_in_flight_id = Column(Integer, ForeignKey("BaggagePricingInFlight.baggage_pricing_in_flight_id"))
    booking_item_id = Column(Integer, ForeignKey("BookingItem.booking_item_id"), unique=True)
    baggage_quantity = Column(Integer)

    baggage_pricing_in_flight = relationship("BaggagePricingInFlight")