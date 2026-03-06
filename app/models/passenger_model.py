from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from .citizenship_model import Citizenship
from .document_type_model import DocumentType

class PassengerDocument(Base):
    __tablename__ = "PassengerDocument"

    passenger_document_id = Column(Integer, primary_key=True)
    passenger_id = Column(Integer, ForeignKey("Passenger.passenger_id"))
    citizenship_id = Column(Integer, ForeignKey("Citizenship.citizenship_id"))
    document_type_id = Column(Integer, ForeignKey("DocumentType.document_type_id"))
    document_number = Column(String)
    document_date_of_issue = Column(Date)
    document_date_of_expire = Column(Date)

    passenger = relationship("Passenger", back_populates="documents")
    citizenship = relationship("Citizenship")  
    document_type = relationship("DocumentType") 

class Passenger(Base):
    __tablename__ = "Passenger"

    passenger_id = Column(Integer, primary_key=True)
    passenger_first_name = Column(String)
    passenger_last_name = Column(String)
    passenger_sex = Column(Boolean)
    passenger_email = Column(String)
    passenger_date_of_birth = Column(Date)

    documents = relationship("PassengerDocument", back_populates="passenger")