from pydantic import BaseModel
from typing import Optional


class AirfleetDTO(BaseModel):
    airfleetId:       int
    aircraftModel:    str
    manufacturerName: Optional[str] = None
    seatCapacity:     Optional[int] = None
    aircraftRangeKm:  Optional[float] = None