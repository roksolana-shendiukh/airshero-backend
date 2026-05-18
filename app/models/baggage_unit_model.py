from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from .base import Base


class BaggageUnit(Base):
    __tablename__ = "BaggageUnit"

    baggage_unit_id              = Column(Integer, primary_key=True)
    boarding_pass_id             = Column(Integer, ForeignKey("BoardingPass.boarding_pass_id"))
    baggage_type_id              = Column(Integer, ForeignKey("BaggageType.baggage_type_id"))
    baggage_unit_tracking_number = Column(String, unique=True)
    baggage_unit_weight_kg       = Column(DECIMAL(5, 2))
    baggage_unit_dimensions      = Column(String)

    baggage_type = relationship("BaggageType")