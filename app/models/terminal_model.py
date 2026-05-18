from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


class TerminalType(Base):
    __tablename__ = "TerminalType"

    terminal_type_id   = Column(Integer, primary_key=True)
    terminal_type_name = Column(String)


class Terminal(Base):
    __tablename__ = "Terminal"

    terminal_id      = Column(Integer, primary_key=True)
    airport_id       = Column(Integer, ForeignKey("Airport.airport_id"))
    terminal_type_id = Column(Integer, ForeignKey("TerminalType.terminal_type_id"))
    terminal_code    = Column(String)
    terminal_size    = Column(DECIMAL(6, 2))

    __table_args__ = (
        UniqueConstraint("airport_id", "terminal_code"),
    )

    terminal_type = relationship("TerminalType")
    gates = relationship("Gate", back_populates="terminal", cascade="all, delete-orphan")
    airport = relationship("Airport", back_populates="terminals")