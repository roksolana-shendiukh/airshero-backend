from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FlightOperationCreateDTO(BaseModel):
    flight_id:   int
    airfleet_id: Optional[int] = None
    gate_id:     Optional[int] = None


class FlightOperationUpdateDTO(BaseModel):
    flight_operation_status_id: Optional[int]      = None
    airfleet_id:                Optional[int]      = None
    gate_id:                    Optional[int]      = None
    flight_operation_state_id:  Optional[int] = None
    actual_departure_date_time: Optional[datetime] = None
    actual_arrival_date_time:   Optional[datetime] = None
    boarding_start_time:        Optional[datetime] = None
    boarding_end_time:          Optional[datetime] = None
    baggage_loading_start_time: Optional[datetime] = None
    baggage_loading_end_time:   Optional[datetime] = None


class FlightOperationDTO(BaseModel):
    flightOperationId:        int
    flightId:                 int
    flightNumber:             Optional[str]      = None
    departsCode:              Optional[str]      = None
    arrivesCode:              Optional[str]      = None
    departsDatetime:          Optional[datetime] = None
    arrivesDdatetime:         Optional[datetime] = None
    statusId:                 int
    statusName:               Optional[str]      = None
    stateDescription: Optional[str] = None
    airfleetId:               Optional[int]      = None
    aircraftModel:            Optional[str]      = None
    gateId:                   Optional[int]      = None
    gateCode:                 Optional[str]      = None
    actualDepartureDatetime:  Optional[str]      = None
    actualArrivalDatetime:    Optional[str]      = None
    boardingStartTime:        Optional[str]      = None
    boardingEndTime:          Optional[str]      = None
    baggageLoadingStartTime:  Optional[str]      = None
    baggageLoadingEndTime:    Optional[str]      = None


class OperationStateRequestDTO(BaseModel):
    state_id:      Optional[int] = None
    custom_reason: Optional[str] = None