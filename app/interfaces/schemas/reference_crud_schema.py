from pydantic import BaseModel
from typing import Optional


class CountryDTO(BaseModel):
    country_name: str


class CityDTO(BaseModel):
    city_name:  str
    country_id: int


class ClassDTO(BaseModel):
    class_name: str


class BaggageTypeDTO(BaseModel):
    baggage_type_name: str


class BaggageRuleDTO(BaseModel):
    baggage_type_id:      int
    baggage_dimension:    Optional[str] = None
    baggage_max_weight:   float
    overweight_fee_per_kg: float


class TerminalTypeDTO(BaseModel):
    terminal_type_name: str