from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


class Gate(Base):
    __tablename__ = "Gate"

    gate_id     = Column(Integer, primary_key=True)
    terminal_id = Column(Integer, ForeignKey("Terminal.terminal_id"))
    gate_code   = Column(String)

    __table_args__ = (
        UniqueConstraint("terminal_id", "gate_code"),
    )

    terminal = relationship("Terminal")