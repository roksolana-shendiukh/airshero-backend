from pydantic import BaseModel
from typing import Optional


class GateDTO(BaseModel):
    gateId:      int
    gateCode:    str
    terminalId:  int
    terminalCode: Optional[str] = None