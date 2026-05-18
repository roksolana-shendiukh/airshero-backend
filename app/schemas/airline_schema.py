from pydantic import BaseModel
from typing import Optional


class AirlineDTO(BaseModel):
    airlineId: int
    airlineName: str
    iataCode: str
    airlineUrl: Optional[str] = None