from pydantic import BaseModel
from typing import List


class BaggageUnitInputDTO(BaseModel):
    baggage_type_id: int
    weight_kg: float
    dimensions: str


class BaggageSurchargeDTO(BaseModel):
    baggage_unit_index: int
    reason: str
    extra_kg: float
    fee_per_kg: float
    total_fee: float


class BaggageCheckDTO(BaseModel):
    surcharges: List[BaggageSurchargeDTO]
    total_surcharge: float
    all_ok: bool