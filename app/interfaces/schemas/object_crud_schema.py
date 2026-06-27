from pydantic import BaseModel
from typing import Optional


class AirportCreateDTO(BaseModel):
    city_id:          int
    airport_name:     str
    airport_address:  str
    airport_code:     str
    latitude:         float
    longitude:        float


class TerminalCreateDTO(BaseModel):
    terminal_type_id: int
    terminal_code:    str
    terminal_size:    Optional[float] = None


class GateCreateDTO(BaseModel):
    gate_code: str


class AirlineCreateDTO(BaseModel):
    country_id:   int
    airline_name: str
    iata_code:    str
    airline_url:  Optional[str] = None


class AirfleetCreateDTO(BaseModel):
    airfleet_manufacturer_id:  int
    aircraft_model:            str
    aircraft_range_km:         float
    aircraft_speed:            float
    seat_capacity:             int
    baggage_capacity:          float
    aircraft_fuel_consumption: Optional[float] = None
    aircraft_url:              Optional[str]   = None


class ManufacturerCreateDTO(BaseModel):
    manufacturer_name: str