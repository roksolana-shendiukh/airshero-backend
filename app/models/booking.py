from pydantic import BaseModel

class FlightClassPriceDTO(BaseModel):
    className: str
    ticketPrice: float


class BaggageOptionDTO(BaseModel):
    baggageType: str
    dimension: str
    maxWeightKg: float
    price: float


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
    classPrices: list[FlightClassPriceDTO]
    baggageOptions: list[BaggageOptionDTO]


class FlightSearchResponseDTO(BaseModel):
    flights: list[FlightResultDTO]
    total: int