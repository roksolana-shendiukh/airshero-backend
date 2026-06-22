from sqlalchemy import Column, Integer, String
from .base import Base

class Citizenship(Base):
    __tablename__ = "Citizenship"

    citizenship_id = Column(Integer, primary_key=True)
    citizenship_name = Column(String)