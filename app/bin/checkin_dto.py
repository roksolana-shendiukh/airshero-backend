from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

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


class SeatDTO(BaseModel):
    seat_layout_id: int
    row: int
    column: str
    class_name: str
    seat_type_name: str
    is_occupied: bool
    is_emergency_exit: bool  

class SeatMapDTO(BaseModel):
    airfleet_model: str
    seats: List[SeatDTO]


class BaggageUnitInputDTO(BaseModel):
    baggage_type_id: int
    weight_kg: float
    dimensions: str 


class BaggageSurchargeDTO(BaseModel):
    baggage_unit_index: int
    reason: str          
    extra_kg: float
    fee_per_kg: float
    total_fee: float


class BaggageCheckDTO(BaseModel):
    surcharges: List[BaggageSurchargeDTO]
    total_surcharge: float
    all_ok: bool


class CheckinPaymentInputDTO(BaseModel):
    payment_method_id: int
    amount: float

class IssueBoardingPassDTO(BaseModel):
    booking_item_id: int
    seat_layout_id: int
    baggage_units: List[BaggageUnitInputDTO] = []
    checkin_payment: Optional[CheckinPaymentInputDTO] = None


class BoardingPassDTO(BaseModel):
    boarding_pass_id: int
    ticket_number: str
    passenger_name: str
    flight_number: str
    departs_datetime: datetime
    arrives_datetime: datetime
    departs_airport_code: str
    arrives_airport_code: str
    seat_row: int
    seat_column: str
    class_name: str
    gate_code: Optional[str]
    terminal_code: Optional[str]
    boarding_start_time: Optional[datetime]
    baggage_count: int
    issued_at: datetime