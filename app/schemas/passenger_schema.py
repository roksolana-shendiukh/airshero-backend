from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from .document_schema import PassengerDocumentDTO


DOC_FORMATS = {
    'PAS': r'^[A-Z]{2}\d{7}$',
    'INT': r'^[A-Z]{2}\d{7}$',
    'OFF': r'^[A-Z]{1}\d{7}$',
    'ID':  r'^\d{9}$',
}


class PassengerDTO(BaseModel):
    passenger_id: Optional[int] = None
    first_name: str
    last_name: str
    sex: Optional[bool] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    documents: Optional[List[PassengerDocumentDTO]] = None


class PassengerCreateDTO(BaseModel):
    first_name: str
    last_name: str
    sex: Optional[bool] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    citizenship_id: Optional[int] = None
    document_type_id: Optional[int] = None
    document_number: Optional[str] = None
    document_date_of_issue: Optional[date] = None
    document_date_of_expire: Optional[date] = None


class PassengerUpdateDTO(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sex: Optional[bool] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    citizenship_id: Optional[int] = None
    document_type_id: Optional[int] = None
    document_number: Optional[str] = None
    document_date_of_issue: Optional[date] = None
    document_date_of_expire: Optional[date] = None