from pydantic import BaseModel
from typing import List


class SeatDTO(BaseModel):
    seat_layout_id: int
    row: int
    column: str
    class_name: str
    seat_type_name: str
    is_occupied: bool
    is_emergency_exit: bool


class SeatMapDTO(BaseModel):
    airfleet_model: str
    seats: List[SeatDTO]