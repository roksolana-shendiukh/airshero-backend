from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FlightOperationCreateDTO(BaseModel):
    schedule_flight_id: int
    airfleet_id:        Optional[int] = None
    gate_id:            Optional[int] = None


class FlightOperationDTO(BaseModel):
    flight_operation_id:        int
    schedule_flight_id:         int
    flight_number:              Optional[str]      = None
    departs_code:               Optional[str]      = None
    arrives_code:               Optional[str]      = None
    departs_datetime:           Optional[datetime] = None
    arrives_datetime:           Optional[datetime] = None
    status_id:                  int
    status_name:                Optional[str]      = None
    state_description:          Optional[str]      = None
    airfleet_id:                Optional[int]      = None
    aircraft_model:             Optional[str]      = None
    gate_id:                    Optional[int]      = None
    gate_code:                  Optional[str]      = None
    actual_departure_datetime:  Optional[str]      = None
    actual_arrival_datetime:    Optional[str]      = None
    boarding_start_time:        Optional[str]      = None
    boarding_end_time:          Optional[str]      = None
    baggage_loading_start_time: Optional[str]      = None
    baggage_loading_end_time:   Optional[str]      = None
    

class FlightOperationUpdateDTO(BaseModel):
    flight_operation_status_id: Optional[int]      = None
    airfleet_id:                Optional[int]      = None
    gate_id:                    Optional[int]      = None
    flight_operation_state_id:  Optional[int]      = None
    actual_departure_date_time: Optional[datetime] = None
    actual_arrival_date_time:   Optional[datetime] = None
    boarding_start_time:        Optional[datetime] = None
    boarding_end_time:          Optional[datetime] = None
    baggage_loading_start_time: Optional[datetime] = None
    baggage_loading_end_time:   Optional[datetime] = None


class OperationStateRequestDTO(BaseModel):
    state_id:      Optional[int] = None
    custom_reason: Optional[str] = None