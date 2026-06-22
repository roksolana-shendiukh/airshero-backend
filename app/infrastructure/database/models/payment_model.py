from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL
from sqlalchemy.orm import relationship
from .base import Base


class PaymentStatus(Base):
    __tablename__ = "PaymentStatus"

    payment_status_id   = Column(Integer, primary_key=True)
    payment_status_name = Column(String)


class PaymentMethod(Base):
    __tablename__ = "PaymentMethod"

    payment_method_id   = Column(Integer, primary_key=True)
    payment_method_name = Column(String)


class Payment(Base):
    __tablename__ = "Payment"

    payment_id        = Column(Integer, primary_key=True)
    booking_id        = Column(Integer, ForeignKey("Booking.booking_id"))
    payment_status_id = Column(Integer, ForeignKey("PaymentStatus.payment_status_id"))
    payment_method_id = Column(Integer, ForeignKey("PaymentMethod.payment_method_id"))
    payment_date_time = Column(DateTime)
    payment_amount    = Column(DECIMAL(8, 2))

    booking        = relationship("Booking", back_populates="payments")
    payment_status = relationship("PaymentStatus")
    payment_method = relationship("PaymentMethod")