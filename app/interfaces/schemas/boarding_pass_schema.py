from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BoardingPassDTO(BaseModel):
    boarding_pass_id: int
    ticket_number: str
    passenger_name: str
    flight_number: str
    departs_datetime: datetime
    arrives_datetime: datetime
    departs_airport_code: str
    arrives_airport_code: str
    seat_row: int
    seat_column: str
    class_name: str
    gate_code: Optional[str]
    terminal_code: Optional[str]
    boarding_start_time: Optional[datetime]
    baggage_count: int
    issued_at: datetime