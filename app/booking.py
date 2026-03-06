from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BaggageItemDTO(BaseModel):
    baggagePricingInFlightId: int
    quantity: int


class BookingPassengerDTO(BaseModel):
    passengerId: Optional[int] = None
    documentId: Optional[int] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    sex: Optional[bool] = None
    dateOfBirth: Optional[str] = None
    citizenshipId: Optional[int] = None
    documentTypeId: Optional[int] = None
    documentNumber: Optional[str] = None
    documentDateOfIssue: Optional[str] = None
    documentDateOfExpire: Optional[str] = None
    flightPriceId: int
    baggageItems: list[BaggageItemDTO] = []


class CreateBookingDTO(BaseModel):
    passengers: list[BookingPassengerDTO]
    totalAmount: float


class BookingResponseDTO(BaseModel):
    bookingId: int
    bookingNumber: str
    expiresAt: datetime


class PaymentDTO(BaseModel):
    paymentMethodId: int
    status: str  
    amount: float