from pydantic import BaseModel
from datetime import date
from typing import Optional


class PassengerDocumentDTO(BaseModel):
    document_id: Optional[int] = None
    citizenship_id: Optional[int] = None
    citizenship_name: Optional[str] = None
    document_type_id: Optional[int] = None
    document_type_name: Optional[str] = None
    document_number: Optional[str] = None
    document_date_of_issue: Optional[date] = None
    document_date_of_expire: Optional[date] = None