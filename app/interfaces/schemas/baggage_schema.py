from pydantic import BaseModel
from typing import List


class BaggageUnitInputDTO(BaseModel):
    baggageTypeId: int
    weightKg:      float
    dimensions:    str


class BaggageSurchargeDTO(BaseModel):
    baggageUnitIndex: int
    reason:           str
    extraKg:          float
    feePerKg:         float
    totalFee:         float


class BaggageCheckDTO(BaseModel):
    surcharges:     List[BaggageSurchargeDTO]
    totalSurcharge: float
    allOk:          bool