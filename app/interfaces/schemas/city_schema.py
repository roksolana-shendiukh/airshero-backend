from pydantic import BaseModel


class CityDTO(BaseModel):
    city_id:      int
    city_name:    str
    country_name: str