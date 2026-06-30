from pydantic import BaseModel
from datetime import date, time
from typing import Optional


class BoardingPassDTO(BaseModel):
    boarding_pass_id:     int
    ticket_number:        str
    passenger_name:       str
    flight_number:        str
    departs_date:         date
    departure_time:       Optional[time] = None
    arrival_time:         Optional[time] = None
    departs_airport_code: str
    arrives_airport_code: str
    seat_row:             int
    seat_column:          str
    class_name:           str
    gate_code:            Optional[str] = None
    terminal_code:        Optional[str] = None
    boarding_start_time:  Optional[time] = None
    baggage_count:        int
    issued_at:            date

    