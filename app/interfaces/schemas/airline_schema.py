from pydantic import BaseModel
from typing import Optional


class AirlineDTO(BaseModel):
    airline_id:   int
    airline_name: str
    iata_code:    str
    airline_url:  Optional[str] = None