from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
from .baggage_schema import BaggageUnitInputDTO


class DocumentInfoDTO(BaseModel):
    document_id: int
    document_number: str
    document_type_name: Optional[str]
    citizenship_name: Optional[str]
    document_date_of_expire: Optional[date]
    is_valid: bool


class BookingItemDTO(BaseModel):
    booking_item_id: int
    passenger_id: int
    first_name: str
    last_name: str
    date_of_birth: Optional[date]
    document: DocumentInfoDTO
    class_name: str
    flight_number: str
    departs_datetime: datetime
    arrives_datetime: datetime
    departs_airport_code: str
    arrives_airport_code: str
    baggage_type_name: Optional[str]
    baggage_quantity: Optional[int]
    baggage_max_weight: Optional[float]
    is_checked_in: bool


class BookingDetailsDTO(BaseModel):
    booking_id: int
    booking_number: str
    booking_status: str
    payment_status: Optional[str]
    total_amount: float
    items: List[BookingItemDTO]


class CheckinPaymentInputDTO(BaseModel):
    payment_method_id: int
    amount: float


class IssueBoardingPassDTO(BaseModel):
    booking_item_id: int
    seat_layout_id: int
    baggage_units: List[BaggageUnitInputDTO] = []
    checkin_payment: Optional[CheckinPaymentInputDTO] = None