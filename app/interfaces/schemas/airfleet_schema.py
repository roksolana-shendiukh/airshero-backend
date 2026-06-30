from pydantic import BaseModel


class AirfleetDTO(BaseModel):
    airfleet_id:               int
    aircraft_model:            str
    manufacturer_name:         str | None = None
    seat_capacity:             int | None = None
    aircraft_range_km:         float | None = None
    aircraft_speed:            float | None = None
    baggage_capacity:          float | None = None
    aircraft_fuel_consumption: float | None = None
    aircraft_url:              str | None = None