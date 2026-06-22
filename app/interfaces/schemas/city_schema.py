from pydantic import BaseModel


class CityDTO(BaseModel):
    cityId: int
    cityName: str
    countryName: str