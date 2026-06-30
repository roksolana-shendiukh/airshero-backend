from pydantic import BaseModel
from typing import Optional


class GateDTO(BaseModel):
    gate_id:       int
    gate_code:     str
    terminal_id:   int
    terminal_code: Optional[str]   = None
    terminal_size: Optional[float] = None
    terminal_type: Optional[str]   = None
    is_available:  bool            = True