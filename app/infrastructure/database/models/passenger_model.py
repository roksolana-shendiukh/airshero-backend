from sqlalchemy import Column, Integer, String, Boolean, Date
from sqlalchemy.orm import relationship
from .base import Base


class Passenger(Base):
    __tablename__ = "Passenger"

    passenger_id            = Column(Integer, primary_key=True)
    passenger_first_name    = Column(String)
    passenger_last_name     = Column(String)
    passenger_sex           = Column(Boolean)
    passenger_email         = Column(String)
    passenger_date_of_birth = Column(Date)

    documents = relationship("PassengerDocument", back_populates="passenger")