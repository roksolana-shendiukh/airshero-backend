from pydantic import BaseModel
from typing import Optional


class PaymentDTO(BaseModel):
    payment_method_id: int
    amount:            float
    status:            str
    email:             Optional[str] = None
    passenger_id:      Optional[int] = None
    booking_id:      Optional[int] = None