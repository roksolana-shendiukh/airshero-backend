from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


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