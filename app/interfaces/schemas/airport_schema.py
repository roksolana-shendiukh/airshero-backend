from pydantic import BaseModel
from typing import Optional


class AirportDTO(BaseModel):
    airportId:      int
    airportName:    str
    airportCode:    str
    airportAddress: Optional[str] = None
    latitude:       Optional[float] = None
    longitude:      Optional[float] = None