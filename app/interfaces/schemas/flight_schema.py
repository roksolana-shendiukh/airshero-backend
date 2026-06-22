from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class FlightResultDTO(BaseModel):
    flightId: int
    flightNumber: str
    airline: str
    fromAirportCode: str
    fromAirportName: str
    toAirportCode: str
    toAirportName: str
    departureDateTime: str
    arrivalDateTime: str
    duration: str
    flightStatus: str


class FlightSearchResponseDTO(BaseModel):
    flights: List[FlightResultDTO]
    total: int


class FlightDTO(BaseModel):
    flightId: int
    flightNumber: str
    departsDatetime: datetime
    arrivesDatetime: datetime
    flightDuration: str
    departsCode: str
    departsAirport: str
    arrivesCode: str
    arrivesAirport: str
    departsCity: str
    arrivesCity: str
    airlineName: str
    airlineLogoUrl: Optional[str] = None
    className: str
    ticketPrice: float

class FlightFilterRequestDTO(BaseModel):
    flightIds: List[int]
    classNames: Optional[List[str]] = None
    minPrice: Optional[float] = None
    maxPrice: Optional[float] = None
    airlineNames: Optional[List[str]] = None
    sortBy: str = "price_asc"
    departureSlots: Optional[List[str]] = None  