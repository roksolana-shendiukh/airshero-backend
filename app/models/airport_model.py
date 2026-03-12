from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from .base import Base

class Airport(Base):
    __tablename__ = "Airport"

    airport_id      = Column(Integer, primary_key=True)
    city_id         = Column(Integer, ForeignKey("City.city_id"))
    airport_name    = Column(String)
    airport_address = Column(String)
    airport_code    = Column(String, unique=True)
    latitude        = Column(Numeric(9, 6))
    longitude       = Column(Numeric(9, 6))