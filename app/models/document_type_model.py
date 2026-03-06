from sqlalchemy import Column, Integer, String
from .base import Base

class DocumentType(Base):
    __tablename__ = "DocumentType"

    document_type_id = Column(Integer, primary_key=True)
    document_type_name = Column(String)
    document_type_code = Column(String)