from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


class CheckInAgent(Base):
    __tablename__ = "CheckInAgent"

    checkin_agent_id           = Column(Integer, primary_key=True)
    airport_id                 = Column(Integer, ForeignKey("Airport.airport_id"))
    checkin_agent_first_name   = Column(String)
    checkin_agent_last_name    = Column(String)
    checkin_agent_phone_number = Column(String)

    airport = relationship("Airport")


class AirfleetManufacturer(Base):
    __tablename__ = "AirfleetManufacturer"

    airfleet_manufacturer_id   = Column(Integer, primary_key=True)
    airfleet_manufacturer_name = Column(String)


class Airfleet(Base):
    __tablename__ = "Airfleet"

    airfleet_id               = Column(Integer, primary_key=True)
    airfleet_manufacturer_id  = Column(Integer, ForeignKey("AirfleetManufacturer.airfleet_manufacturer_id"))
    aircraft_range_km         = Column(DECIMAL(7, 2))
    aircraft_model            = Column(String)
    aircraft_speed            = Column(DECIMAL(7, 2))
    seat_capacity             = Column(Integer)
    baggage_capacity          = Column(DECIMAL(7, 2))
    aircraft_fuel_consumption = Column(DECIMAL(6, 2))


class SeatType(Base):
    __tablename__ = "SeatType"

    seat_type_id   = Column(Integer, primary_key=True)
    seat_type_name = Column(String)


class SeatLayout(Base):
    __tablename__ = "SeatLayout"

    seat_layout_id      = Column(Integer, primary_key=True)
    seat_type_id        = Column(Integer, ForeignKey("SeatType.seat_type_id"))
    class_id            = Column(Integer, ForeignKey("Class.class_id"))
    airfleet_id         = Column(Integer, ForeignKey("Airfleet.airfleet_id"))
    seat_layout_rows    = Column(Integer)
    seat_layout_columns = Column(String)

    __table_args__ = (
        UniqueConstraint("airfleet_id", "seat_layout_rows", "seat_layout_columns"),
    )

    seat_type = relationship("SeatType")
    cls       = relationship("Class")
    airfleet  = relationship("Airfleet")


class TerminalType(Base):
    __tablename__ = "TerminalType"

    terminal_type_id   = Column(Integer, primary_key=True)
    terminal_type_name = Column(String)


class Terminal(Base):
    __tablename__ = "Terminal"

    terminal_id      = Column(Integer, primary_key=True)
    airport_id       = Column(Integer, ForeignKey("Airport.airport_id"))
    terminal_type_id = Column(Integer, ForeignKey("TerminalType.terminal_type_id"))
    terminal_code    = Column(String)
    terminal_size    = Column(DECIMAL(6, 2))

    __table_args__ = (
        UniqueConstraint("airport_id", "terminal_code"),
    )

    gates = relationship("Gate")


class Gate(Base):
    __tablename__ = "Gate"

    gate_id     = Column(Integer, primary_key=True)
    terminal_id = Column(Integer, ForeignKey("Terminal.terminal_id"))
    gate_code   = Column(String)

    __table_args__ = (
        UniqueConstraint("terminal_id", "gate_code"),
    )

    terminal = relationship("Terminal")


class FlightOperationStatus(Base):
    __tablename__ = "FlightOperationStatus"

    flight_operation_status_id   = Column(Integer, primary_key=True)
    flight_operation_status_name = Column(String)


class FlightOperation(Base):
    __tablename__ = "FlightOperation"

    flight_operation_id        = Column(Integer, primary_key=True)
    flight_id                  = Column(Integer, ForeignKey("Flight.flight_id"), unique=True)
    flight_operation_status_id = Column(Integer, ForeignKey("FlightOperationStatus.flight_operation_status_id"))
    airfleet_id                = Column(Integer, ForeignKey("Airfleet.airfleet_id"))
    gate_id                    = Column(Integer, ForeignKey("Gate.gate_id"))
    actual_departure_date_time = Column(DateTime)
    actual_arrival_date_time   = Column(DateTime)
    boarding_start_time        = Column(DateTime)
    boarding_end_time          = Column(DateTime)
    baggage_loading_start_time = Column(DateTime)
    baggage_loading_end_time   = Column(DateTime)

    flight   = relationship("Flight")
    status   = relationship("FlightOperationStatus")
    airfleet = relationship("Airfleet")
    gate     = relationship("Gate")


class BoardingPass(Base):
    __tablename__ = "BoardingPass"

    boarding_pass_id              = Column(Integer, primary_key=True)
    checkin_agent_id              = Column(Integer, ForeignKey("CheckInAgent.checkin_agent_id"))
    seat_layout_id                = Column(Integer, ForeignKey("SeatLayout.seat_layout_id"))
    booking_item_id               = Column(Integer, ForeignKey("BookingItem.booking_item_id"), unique=True)
    flight_operation_id           = Column(Integer, ForeignKey("FlightOperation.flight_operation_id"))
    boarding_pass_ticket_number   = Column(String, unique=True)
    boarding_pass_issue_date_time = Column(DateTime)

    __table_args__ = (
        UniqueConstraint("flight_operation_id", "seat_layout_id"),
    )

    checkin_agent    = relationship("CheckInAgent")
    seat_layout      = relationship("SeatLayout")
    booking_item     = relationship("BookingItem")
    flight_operation = relationship("FlightOperation")
    baggage_units    = relationship("BaggageUnit")


class BaggageUnit(Base):
    __tablename__ = "BaggageUnit"

    baggage_unit_id              = Column(Integer, primary_key=True)
    boarding_pass_id             = Column(Integer, ForeignKey("BoardingPass.boarding_pass_id"))
    baggage_type_id              = Column(Integer, ForeignKey("BaggageType.baggage_type_id"))
    baggage_unit_tracking_number = Column(String, unique=True)
    baggage_unit_weight_kg       = Column(DECIMAL(5, 2))
    baggage_unit_dimensions      = Column(String)

    baggage_type = relationship("BaggageType")


class CheckinInPayment(Base):
    __tablename__ = "CheckinInPayment"

    checkin_payment_id        = Column(Integer, primary_key=True)
    payment_status_id         = Column(Integer, ForeignKey("PaymentStatus.payment_status_id"))
    payment_method_id         = Column(Integer, ForeignKey("PaymentMethod.payment_method_id"))
    checkin_payment_date_time = Column(DateTime)
    checkin_payment_amount    = Column(DECIMAL(8, 2))

    payment_status = relationship("PaymentStatus")
    payment_method = relationship("PaymentMethod")