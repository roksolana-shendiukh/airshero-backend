from pydantic import BaseModel


class ClassPriceDTO(BaseModel):
    class_id: int
    price:    float


class CreateFlightDTO(BaseModel):
    schedule_flight_id: int
    departs_datetime:   str
    arrives_datetime:   str
    class_prices:       list[ClassPriceDTO]


class ConfigureFlightDTO(BaseModel):
    class_prices: list[ClassPriceDTO]


class FlightBaggageOptionDTO(BaseModel):
    class_id:               int
    baggage_pricing_rule_id: int
    price:                  float


class AddFlightBaggageDTO(BaseModel):
    baggage_options: list[FlightBaggageOptionDTO]


class ScheduleGroupDTO(BaseModel):
    day_ids:        list[int]
    departure_time: str


class CreateRouteDTO(BaseModel):
    airfleet_id:       int
    departs_airport_id: int
    arrives_airport_id: int
    flight_number:      str | None = None
    schedule_groups:    list[ScheduleGroupDTO]
    flight_start_date:  str
    flight_end_date:    str


class CreateScheduleDTO(BaseModel):
    schedule_groups:   list[ScheduleGroupDTO]
    flight_start_date: str
    flight_end_date:   str


class ConfirmFlightsDTO(BaseModel):
    flight_ids: list[int]


class UpdateFlightClassesDTO(BaseModel):
    class_ids: list[int]


class UpdateFlightTimesDTO(BaseModel):
    departs_datetime: str
    arrives_datetime: str