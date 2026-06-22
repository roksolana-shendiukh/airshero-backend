from sqlalchemy import Column, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from .base import Base


class FlightSchedule(Base):
    __tablename__ = "FlightSchedule"

    flight_schedule_id = Column(Integer, primary_key=True)
    route_id           = Column(Integer, ForeignKey("Route.route_id"))
    flight_start_date  = Column(Date)
    flight_end_date    = Column(Date)

    route = relationship("Route")