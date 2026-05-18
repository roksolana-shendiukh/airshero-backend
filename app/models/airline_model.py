from sqlalchemy import Column, Integer, String, ForeignKey
from .base import Base


class Airline(Base):
    __tablename__ = "Airline"

    airline_id   = Column(Integer, primary_key=True)
    country_id   = Column(Integer, ForeignKey("Country.country_id"))
    airline_name = Column(String)
    iata_code    = Column(String, unique=True)
    airline_url  = Column(String)