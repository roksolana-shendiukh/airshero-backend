from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BaggageItemDTO(BaseModel):
    baggage_pricing_in_flight_id: int
    quantity: int


class BookingPassengerDTO(BaseModel):
    passenger_id: Optional[int] = None
    document_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sex: Optional[bool] = None
    date_of_birth: Optional[str] = None
    citizenship_id: Optional[int] = None
    document_type_id: Optional[int] = None
    document_number: Optional[str] = None
    document_date_of_issue: Optional[str] = None
    document_date_of_expire: Optional[str] = None
    flight_price_id: int
    return_flight_price_id: Optional[int] = None
    baggage_items: list[BaggageItemDTO] = []


class CreateBookingDTO(BaseModel):
    passengers: list[BookingPassengerDTO]
    total_amount: float


class CreateGroupBookingDTO(BaseModel):
    booking1: CreateBookingDTO
    booking2: CreateBookingDTO


class BookingResponseDTO(BaseModel):
    bookingId: int
    bookingNumber: str
    expiresAt: datetime


class GroupBookingResponseDTO(BaseModel):
    booking1: BookingResponseDTO
    booking2: BookingResponseDTO
    expiresAt: datetime


class PaymentDTO(BaseModel):
    paymentMethodId: int
    status: str
    amount: float