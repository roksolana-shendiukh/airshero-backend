from pydantic import BaseModel


class ClassPriceDTO(BaseModel):
    class_id: int
    price: float


class CreateFlightDTO(BaseModel):
    flightScheduleId: int
    departsDatetime: str
    arrivesDatetime: str
    classPrices: list[ClassPriceDTO]

class ConfigureFlightDTO(BaseModel):
    classPrices: list[ClassPriceDTO]


class FlightBaggageOptionDTO(BaseModel):
    classId: int
    baggagePricingRuleId: int
    price: float


class AddFlightBaggageDTO(BaseModel):
    baggageOptions: list[FlightBaggageOptionDTO]


class ScheduleGroupDTO(BaseModel):
    dayIds: list[int]
    departureTime: str


class CreateRouteDTO(BaseModel):
    airfleetId: int
    departsAirportId: int
    arrivesAirportId: int
    flightNumber: str | None = None
    scheduleGroups: list[ScheduleGroupDTO]
    flightStartDate: str
    flightEndDate: str


class CreateScheduleDTO(BaseModel):
    scheduleGroups: list[ScheduleGroupDTO]
    flightStartDate: str
    flightEndDate: str


class ConfirmFlightsDTO(BaseModel):
    flightIds: list[int]

class UpdateFlightClassesDTO(BaseModel):
    classIds: list[int]


    