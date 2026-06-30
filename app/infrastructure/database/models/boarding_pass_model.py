from __future__ import annotations
import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, text
from sqlalchemy.dialects.mssql import DATETIME2
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .checkin_model import CheckInAgentFlightOperation
    from .baggage_model import BaggageUnit


class BoardingPass(Base):
    __tablename__ = 'BoardingPass'
    __table_args__ = (
        ForeignKeyConstraint(['checkInAgent_flightOperation_id'], ['CheckInAgentFlightOperation.checkInAgent_flightOperation_id'], name='FK_BoardingPass_CheckInAgentFlightOperation'),
        PrimaryKeyConstraint('boarding_pass_id', name='PK__Boarding__42CCA949115FBC5C'),
        Index('UQ_BoardingPass_Agent_Seat', 'checkInAgent_flightOperation_id', 'seat_layout_id', mssql_clustered=False, unique=True),
        Index('UQ__Boarding__E577F61D43F17E9F', 'booking_item_id', mssql_clustered=False, unique=True),
    )

    boarding_pass_id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1), primary_key=True, autoincrement=True)
    checkInAgent_flightOperation_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('((0))'))
    boarding_pass_ticket_number: Mapped[str] = mapped_column(String(15, 'SQL_Latin1_General_CP1_CI_AS'), nullable=False)
    seat_layout_id: Mapped[Optional[int]] = mapped_column(Integer)
    booking_item_id: Mapped[Optional[int]] = mapped_column(Integer)
    boarding_pass_issue_date_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2, server_default=text('(getdate())'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DATETIME2)

    checkInAgent_flightOperation: Mapped['CheckInAgentFlightOperation'] = relationship('CheckInAgentFlightOperation', back_populates='BoardingPass')
    BaggageUnit: Mapped[list['BaggageUnit']] = relationship('BaggageUnit', back_populates='boarding_pass')