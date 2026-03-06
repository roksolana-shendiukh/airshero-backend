from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, DECIMAL
from sqlalchemy.orm import relationship
from .base import Base


class BookingStatus(Base):
    __tablename__ = "BookingStatus"

    booking_status_id = Column(Integer, primary_key=True)
    booking_status_name = Column(String)


class Booking(Base):
    __tablename__ = "Booking"

    booking_id = Column(Integer, primary_key=True)
    booking_status_id = Column(Integer, ForeignKey("BookingStatus.booking_status_id"))
    booking_date_time = Column(DateTime)
    booking_total_amount = Column(DECIMAL(10, 2))
    booking_number = Column(String, unique=True)

    status = relationship("BookingStatus")
    items = relationship("BookingItem", back_populates="booking")
    payments = relationship("Payment", back_populates="booking")


class BookingItem(Base):
    __tablename__ = "BookingItem"

    booking_item_id = Column(Integer, primary_key=True)
    passenger_document_id = Column(Integer, ForeignKey("PassengerDocument.passenger_document_id"))
    booking_id = Column(Integer, ForeignKey("Booking.booking_id"))
    flight_price_id = Column(Integer, ForeignKey("FlightPrice.flight_price_id"))

    booking = relationship("Booking", back_populates="items")
    passenger_document = relationship("PassengerDocument")
    flight_price = relationship("FlightPrice")
    baggage_option = relationship("BaggageOptionInFlight", uselist=False)
boarding_pass = relationship("BoardingPass", uselist=False)


class PaymentStatus(Base):
    __tablename__ = "PaymentStatus"

    payment_status_id = Column(Integer, primary_key=True)
    payment_status_name = Column(String)


class PaymentMethod(Base):
    __tablename__ = "PaymentMethod"

    payment_method_id = Column(Integer, primary_key=True)
    payment_method_name = Column(String)


class Payment(Base):
    __tablename__ = "Payment"

    payment_id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("Booking.booking_id"))
    payment_status_id = Column(Integer, ForeignKey("PaymentStatus.payment_status_id"))
    payment_method_id = Column(Integer, ForeignKey("PaymentMethod.payment_method_id"))
    payment_date_time = Column(DateTime)
    payment_amount = Column(DECIMAL(8, 2))

    booking = relationship("Booking", back_populates="payments")
    payment_status = relationship("PaymentStatus")
    payment_method = relationship("PaymentMethod")