from pydantic import BaseModel


class ClassPriceDTO(BaseModel):
    class_id: int
    price: float


class CreateFlightDTO(BaseModel):
    flightScheduleId: int
    departsDatetime: str
    arrivesDatetime: str
    classPrices: list[ClassPriceDTO]

class FlightBaggageOptionDTO(BaseModel):
    classId: int                
    baggagePricingRuleId: int   
    price: float               

class AddFlightBaggageDTO(BaseModel):
    baggageOptions: list[FlightBaggageOptionDTO]