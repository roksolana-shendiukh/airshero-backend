from pydantic import BaseModel
from typing import Optional


class PaymentDTO(BaseModel):
    paymentMethodId: int
    amount: float
    status: str
    email: Optional[str] = None
    passengerId: Optional[int] = None