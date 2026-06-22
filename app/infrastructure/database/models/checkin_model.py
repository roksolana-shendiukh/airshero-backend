from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL
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


class CheckinInPayment(Base):
    __tablename__ = "CheckinInPayment"

    checkin_payment_id        = Column(Integer, primary_key=True)
    payment_status_id         = Column(Integer, ForeignKey("PaymentStatus.payment_status_id"))
    payment_method_id         = Column(Integer, ForeignKey("PaymentMethod.payment_method_id"))
    checkin_payment_date_time = Column(DateTime)
    checkin_payment_amount    = Column(DECIMAL(8, 2))

    payment_status = relationship("PaymentStatus")
    payment_method = relationship("PaymentMethod")