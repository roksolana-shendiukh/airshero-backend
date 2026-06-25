from pydantic import BaseModel
from typing import Optional


class CrewCreateDTO(BaseModel):
    first_name:       str
    last_name:        str
    position_id:      int
    license_type_id:  int
    experience_years: int


class CrewUpdateDTO(BaseModel):
    first_name:       Optional[str] = None
    last_name:        Optional[str] = None
    position_id:      Optional[int] = None
    license_type_id:  Optional[int] = None
    experience_years: Optional[int] = None