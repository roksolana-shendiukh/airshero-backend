from pydantic import BaseModel
from typing import Optional


class AirportDTO(BaseModel):
    airport_id:      int
    airport_name:    str
    airport_code:    str
    airport_address: Optional[str] = None
    latitude:        Optional[float] = None
    longitude:       Optional[float] = None