from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class FlightResultDTO(BaseModel):
    flight_id:           int
    flight_number:       str
    airline:             str
    from_airport_code:   str
    from_airport_name:   str
    to_airport_code:     str
    to_airport_name:     str
    departure_date_time: str
    arrival_date_time:   str
    duration:            str
    flight_status:       str


class FlightSearchResponseDTO(BaseModel):
    flights: List[FlightResultDTO]
    total:   int


class FlightDTO(BaseModel):
    flight_id:        int
    flight_number:    str
    departs_datetime: datetime
    arrives_datetime: datetime
    flight_duration:  str
    departs_code:     str
    departs_airport:  str
    arrives_code:     str
    arrives_airport:  str
    departs_city:     str
    arrives_city:     str
    airline_name:     str
    airline_logo_url: Optional[str] = None
    class_name:       str
    ticket_price:     float


class FlightFilterRequestDTO(BaseModel):
    flight_ids:      List[int]
    class_names:     Optional[List[str]]  = None
    min_price:       Optional[float]      = None
    max_price:       Optional[float]      = None
    airline_names:   Optional[List[str]]  = None
    sort_by:         str                  = "price_asc"
    departure_slots: Optional[List[str]]  = None

    