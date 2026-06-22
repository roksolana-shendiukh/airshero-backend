from sqlalchemy import Column, Integer, String
from .base import Base


class Country(Base):
    __tablename__ = "Country"

    country_id   = Column(Integer, primary_key=True)
    country_name = Column(String)