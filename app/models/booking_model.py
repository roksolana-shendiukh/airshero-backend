from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL
from sqlalchemy.orm import relationship
from .base import Base


class BookingStatus(Base):
    __tablename__ = "BookingStatus"

    booking_status_id   = Column(Integer, primary_key=True)
    booking_status_name = Column(String)


class Booking(Base):
    __tablename__ = "Booking"

    booking_id           = Column(Integer, primary_key=True)
    booking_status_id    = Column(Integer, ForeignKey("BookingStatus.booking_status_id"))
    booking_date_time    = Column(DateTime)
    booking_total_amount = Column(DECIMAL(10, 2))
    booking_number       = Column(String, unique=True)

    status   = relationship("BookingStatus")
    items    = relationship("BookingItem", back_populates="booking")
    payments = relationship("Payment", back_populates="booking")


class BookingItem(Base):
    __tablename__ = "BookingItem"

    booking_item_id       = Column(Integer, primary_key=True)
    passenger_document_id = Column(Integer, ForeignKey("PassengerDocument.passenger_document_id"))
    booking_id            = Column(Integer, ForeignKey("Booking.booking_id"))
    flight_price_id       = Column(Integer, ForeignKey("FlightPrice.flight_price_id"))

    booking            = relationship("Booking", back_populates="items")
    passenger_document = relationship("PassengerDocument")
    flight_price       = relationship("FlightPrice")
    baggage_option     = relationship("BaggageOptionInFlight", uselist=False)
    boarding_pass      = relationship("BoardingPass", uselist=False)