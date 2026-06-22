from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from .base import Base


class DocumentType(Base):
    __tablename__ = "DocumentType"

    document_type_id   = Column(Integer, primary_key=True)
    document_type_name = Column(String)
    document_type_code = Column(String)


class PassengerDocument(Base):
    __tablename__ = "PassengerDocument"

    passenger_document_id   = Column(Integer, primary_key=True)
    passenger_id            = Column(Integer, ForeignKey("Passenger.passenger_id"))
    citizenship_id          = Column(Integer, ForeignKey("Citizenship.citizenship_id"))
    document_type_id        = Column(Integer, ForeignKey("DocumentType.document_type_id"))
    document_number         = Column(String)
    document_date_of_issue  = Column(Date)
    document_date_of_expire = Column(Date)

    passenger     = relationship("Passenger", back_populates="documents")
    citizenship   = relationship("Citizenship")
    document_type = relationship("DocumentType")

    