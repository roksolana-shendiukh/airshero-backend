from pydantic import BaseModel


class AirfleetDTO(BaseModel):
    airfleetId:              int
    aircraftModel:           str
    manufacturerName:        str | None = None
    seatCapacity:            int | None = None
    aircraftRangeKm:         float | None = None
    aircraftSpeed:           float | None = None
    baggageCapacity:         float | None = None
    aircraftFuelConsumption: float | None = None
    aircraftUrl:             str | None = None