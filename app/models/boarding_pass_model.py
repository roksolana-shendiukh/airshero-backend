from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


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