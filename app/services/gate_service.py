from sqlalchemy.orm import Session
from app.repositories import gate_repository
from app.schemas.gate_schema import GateDTO


def get_all_gates(db: Session, airport_id: int | None = None) -> list[GateDTO]:
    return [
        GateDTO(
            gateId=g.gate_id,
            gateCode=g.gate_code,
            terminalId=g.terminal_id,
            terminalCode=getattr(g.terminal, 'terminal_code', None),
        )
        for g in gate_repository.get_all(db, airport_id=airport_id)
    ]