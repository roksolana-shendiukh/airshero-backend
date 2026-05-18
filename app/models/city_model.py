from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class City(Base):
    __tablename__ = "City"

    city_id    = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("Country.country_id"))
    city_name  = Column(String)

    country = relationship("Country")