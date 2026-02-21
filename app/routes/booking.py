from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.dependencies.auth import require_role
from app.database import get_db
from app.models.booking import (
    FlightResultDTO,
    FlightSearchResponseDTO,
    FlightClassPriceDTO,
    BaggageOptionDTO,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


FLIGHT_SEARCH_QUERY = text("""
    SELECT DISTINCT
        f.flight_id,
        r.flight_number,
        al.airline_name,
        dep_ap.airport_code   AS from_airport_code,
        dep_ap.airport_name   AS from_airport_name,
        arr_ap.airport_code   AS to_airport_code,
        arr_ap.airport_name   AS to_airport_name,
        f.departs_datetime,
        f.arrives_datetime,
        r.flight_duration,
        fs_stat.flight_status_name
    FROM Flight f
    JOIN FlightSchedule fsch  ON f.flight_schedule_id = fsch.flight_schedule_id
    JOIN Route r              ON fsch.route_id = r.route_id
    JOIN Airline al           ON r.airline_id = al.airline_id
    JOIN Airport dep_ap       ON r.departs_airport_id = dep_ap.airport_id
    JOIN Airport arr_ap       ON r.arrives_airport_id = arr_ap.airport_id
    JOIN FlightStatus fs_stat ON f.flight_status_id = fs_stat.flight_status_id
    WHERE
        (dep_ap.airport_code = :from_code OR dep_ap.airport_name LIKE :from_name)
        AND (arr_ap.airport_code = :to_code OR arr_ap.airport_name LIKE :to_name)
        AND CAST(f.departs_datetime AS DATE) = :depart_date
        AND fs_stat.flight_status_name NOT IN ('Cancelled', 'Completed')
    ORDER BY f.departs_datetime
""")

CLASS_PRICES_QUERY = text("""
    SELECT
        c.class_name,
        fp.ticket_price
    FROM FlightPrice fp
    JOIN Class c ON fp.class_id = c.class_id
    WHERE fp.flight_id = :flight_id
    ORDER BY fp.ticket_price
""")

BAGGAGE_OPTIONS_QUERY = text("""
    SELECT
        bt.baggage_type_name,
        bpr.baggage_dimension,
        bpr.baggage_max_weight,
        bpf.baggage_price
    FROM BaggagePricingInFlight bpf
    JOIN BaggagePricingRule bpr ON bpf.baggage_pricing_rule_id = bpr.baggage_pricing_rule_id
    JOIN BaggageType bt         ON bpr.baggage_type_id = bt.baggage_type_id
    WHERE bpf.flight_id = :flight_id
    ORDER BY bpf.baggage_price
""")

@router.get("/search", response_model=FlightSearchResponseDTO)
def search_flights(
    from_airport: str = Query(..., alias="from", min_length=2, max_length=100),
    to_airport: str = Query(..., alias="to", min_length=2, max_length=100),
    depart_date: date = Query(..., alias="departDate"),
    return_date: Optional[date] = Query(None, alias="returnDate"),
    adults: int = Query(1, ge=1, le=6),
    children: int = Query(0, ge=0, le=5),
    infants: int = Query(0, ge=0, le=5),
    db: Session = Depends(get_db),
    user=Depends(require_role("salesAgent")),
):
    if adults + children + infants > 6:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["query", "adults"], "msg": "Total passengers cannot exceed 6"}],
        )

    rows = db.execute(FLIGHT_SEARCH_QUERY, {
        "from_code": from_airport.upper(),
        "from_name": f"%{from_airport}%",
        "to_code": to_airport.upper(),
        "to_name": f"%{to_airport}%",
        "depart_date": depart_date,
    }).fetchall()

    flights = []
    for row in rows:
        flight_id = row.flight_id

        class_prices = db.execute(CLASS_PRICES_QUERY, {"flight_id": flight_id}).fetchall()
        baggage_options = db.execute(BAGGAGE_OPTIONS_QUERY, {"flight_id": flight_id}).fetchall()

        duration_raw = row.flight_duration
        if hasattr(duration_raw, "seconds"):
            total_minutes = duration_raw.seconds // 60
            hours, minutes = divmod(total_minutes, 60)
            duration_str = f"{hours}h {minutes}m"
        else:
            duration_str = str(duration_raw)

        flights.append(FlightResultDTO(
            flightId=flight_id,
            flightNumber=row.flight_number,
            airline=row.airline_name,
            fromAirportCode=row.from_airport_code,
            fromAirportName=row.from_airport_name,
            toAirportCode=row.to_airport_code,
            toAirportName=row.to_airport_name,
            departureDateTime=row.departs_datetime.strftime("%Y-%m-%dT%H:%M"),
            arrivalDateTime=row.arrives_datetime.strftime("%Y-%m-%dT%H:%M"),
            duration=duration_str,
            flightStatus=row.flight_status_name,
            classPrices=[
                FlightClassPriceDTO(
                    className=cp.class_name,
                    ticketPrice=float(cp.ticket_price),
                )
                for cp in class_prices
            ],
            baggageOptions=[
                BaggageOptionDTO(
                    baggageType=bo.baggage_type_name,
                    dimension=bo.baggage_dimension,
                    maxWeightKg=float(bo.baggage_max_weight),
                    price=float(bo.baggage_price),
                )
                for bo in baggage_options
            ],
        ))

    return FlightSearchResponseDTO(flights=flights, total=len(flights))