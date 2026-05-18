from pydantic import BaseModel
from typing import Optional


class GateDTO(BaseModel):
    gateId:       int
    gateCode:     str
    terminalId:   int
    terminalCode: Optional[str]   = None
    terminalSize: Optional[float] = None
    terminalType: Optional[str]   = None
    isAvailable:  bool            = True