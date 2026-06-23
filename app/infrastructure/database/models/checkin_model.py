import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKeyConstraint, Identity, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CheckInAgent(Base):
    __tablename__ = 'CheckInAgent'
    __table_args__ = (
        ForeignKeyConstraint(['airport_id'], ['Airport.airport_id'], name='FKCheckInAgentAirport'),
        PrimaryKeyConstraint('checkin_agent_id', name='PK__CheckInA__C2852D03C7D8F40E'),
    )

    checkin_agent_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    airport_id: Mapped[Optional[int]] = mapped_column(Integer)
    checkin_agent_first_name: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    checkin_agent_last_name: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    checkin_agent_phone_number: Mapped[Optional[str]] = mapped_column(String(30, 'SQL_Latin1_General_CP1_CI_AS'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    airport: Mapped[Optional['Airport']] = relationship('Airport', back_populates='CheckInAgent')
    CheckInAgentFlightOperation: Mapped[list['CheckInAgentFlightOperation']] = relationship('CheckInAgentFlightOperation', back_populates='checkin_agent')


class CheckInAgentFlightOperation(Base):
    __tablename__ = 'CheckInAgentFlightOperation'
    __table_args__ = (
        ForeignKeyConstraint(['checkin_agent_id'], ['CheckInAgent.checkin_agent_id'], name='FK_CheckInAgentFlightOperation_CheckInAgent'),
        ForeignKeyConstraint(['flight_operation_id'], ['FlightOperation.flight_operation_id'], name='FK_CheckInAgentFlightOperation_FlightOperation'),
        PrimaryKeyConstraint('checkInAgent_flightOperation_id', name='PK_CheckInAgentFlightOperation'),
    )

    checkInAgent_flightOperation_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    checkin_agent_id: Mapped[int] = mapped_column(Integer, nullable=False)
    flight_operation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    start_work_datetime: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    end_work_datetime: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    checkin_agent: Mapped['CheckInAgent'] = relationship('CheckInAgent', back_populates='CheckInAgentFlightOperation')
    flight_operation: Mapped['FlightOperation'] = relationship('FlightOperation', back_populates='CheckInAgentFlightOperation')
    BoardingPass: Mapped[list['BoardingPass']] = relationship('BoardingPass', back_populates='checkInAgent_flightOperation')