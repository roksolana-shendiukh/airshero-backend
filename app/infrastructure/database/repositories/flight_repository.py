from sqlalchemy.orm import Session
from sqlalchemy import text


def get_flight_availability(db: Session, flight_id: int) -> list:
    sql = text("""
        SELECT class_name, total_seats, booked_seats, available_seats
        FROM FN_GetFlightAvailability(:flight_id)
    """)
    return db.execute(sql, {"flight_id": flight_id}).fetchall()


def search_flights(db: Session, from_city: int, to_city: int, depart_date: str):
    result = db.execute(
        text("EXEC SP_SearchFlights :departs_city_id, :arrives_city_id, :departs_date"),
        {
            "departs_city_id": from_city,
            "arrives_city_id": to_city,
            "departs_date":    depart_date,
        }
    )
    return result.mappings().all()


def filter_flights_by_ids(
    db: Session,
    flight_ids: list[int],
    class_names: list[str] | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    airline_names: list[str] | None = None,
    sort_by: str = "price_asc",
    departure_slots: list[str] | None = None,
):
    if not flight_ids:
        return []

    params: dict = {}

    flight_placeholders = ", ".join(f":fid_{i}" for i in range(len(flight_ids)))
    for i, fid in enumerate(flight_ids):
        params[f"fid_{i}"] = fid

    # ✅ фільтруємо по schedule_flight_id (повертає SP_SearchFlights)
    conditions = [f"sf.schedule_flight_id IN ({flight_placeholders})"]

    if class_names:
        class_placeholders = ", ".join(f":cls_{i}" for i in range(len(class_names)))
        for i, cls in enumerate(class_names):
            params[f"cls_{i}"] = cls
        conditions.append(f"c.class_name IN ({class_placeholders})")

    if min_price is not None:
        conditions.append("fp.ticket_price >= :min_price")
        params["min_price"] = min_price

    if max_price is not None:
        conditions.append("fp.ticket_price <= :max_price")
        params["max_price"] = max_price

    if airline_names:
        airline_placeholders = ", ".join(f":aln_{i}" for i in range(len(airline_names)))
        for i, aln in enumerate(airline_names):
            params[f"aln_{i}"] = aln
        conditions.append(f"al.airline_name IN ({airline_placeholders})")

    # ✅ час вильоту береться з ScheduledFlight.departs_date
    # (якщо потрібна фільтрація по годині — уточни чи є час окремо)
    slot_map = {
        "night":     "(DATEPART(HOUR, fo.actual_departure_date_time) >= 0  AND DATEPART(HOUR, fo.actual_departure_date_time) < 6)",
        "morning":   "(DATEPART(HOUR, fo.actual_departure_date_time) >= 6  AND DATEPART(HOUR, fo.actual_departure_date_time) < 12)",
        "afternoon": "(DATEPART(HOUR, fo.actual_departure_date_time) >= 12 AND DATEPART(HOUR, fo.actual_departure_date_time) < 18)",
        "evening":   "(DATEPART(HOUR, fo.actual_departure_date_time) >= 18 AND DATEPART(HOUR, fo.actual_departure_date_time) < 24)",
    }
    if departure_slots:
        slot_clauses = [slot_map[s] for s in departure_slots if s in slot_map]
        if slot_clauses:
            conditions.append(f"({ ' OR '.join(slot_clauses) })")

    order = {
        "price_asc":  "fp.ticket_price ASC",
        "price_desc": "fp.ticket_price DESC",
    }.get(sort_by, "fp.ticket_price ASC")

    where = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            f.flight_id,
            sf.schedule_flight_id,
            fc.flight_class_id,
            fp.flight_price_id,
            f.flight_number,
            dep_air.airport_name    AS departure_airport_name,
            dep_air.airport_code    AS departure_airport_code,
            arr_air.airport_name    AS arrival_airport_name,
            arr_air.airport_code    AS arrival_airport_code,
            sf.departs_date,
            f.flight_duration,
            c.class_name,
            fp.ticket_price,
            fs.flight_status_name,
            al.airline_name,
            al.airline_url          AS airline_logo_url
        FROM ScheduledFlight sf
        INNER JOIN FlightStatus fs
               ON fs.flight_status_id    = sf.flight_status_id
        INNER JOIN Flight f
               ON f.flight_id            = sf.flight_id
        INNER JOIN Airline al
               ON al.airline_id          = f.airline_id
        INNER JOIN Route r
               ON r.route_id             = f.route_id
        INNER JOIN Airport dep_air
               ON dep_air.airport_id     = r.departs_airport_id
        INNER JOIN Airport arr_air
               ON arr_air.airport_id     = r.arrives_airport_id
        INNER JOIN FlightClass fc
               ON fc.flight_id           = f.flight_id
        INNER JOIN Class c
               ON c.class_id             = fc.class_id
        INNER JOIN FlightPrice fp
               ON fp.flight_class_id     = fc.flight_class_id
              AND fp.schedule_flight_id  = sf.schedule_flight_id
              AND fp.flight_published_date = (
                    SELECT MAX(fp2.flight_published_date)
                    FROM FlightPrice fp2
                    WHERE fp2.flight_class_id    = fc.flight_class_id
                      AND fp2.schedule_flight_id = sf.schedule_flight_id
              )
        LEFT JOIN FlightOperation fo
               ON fo.schedule_flight_id  = sf.schedule_flight_id
        WHERE {where}
        ORDER BY {order}, sf.departs_date ASC
    """)

    result = db.execute(sql, params)
    return result.mappings().all()


def get_flights_without_operation(db: Session, airline_id: int):
    sql = text("""
        SELECT
            f.flight_id,
            sf.schedule_flight_id,
            f.flight_number,
            dep_air.airport_id      AS departs_airport_id,
            dep_air.airport_code    AS departs_code,
            arr_air.airport_code    AS arrives_code,
            sf.departs_date,
            f.flight_duration,
            fs.flight_status_name,
            al.airline_name
        FROM ScheduledFlight sf
        INNER JOIN FlightStatus fs
               ON fs.flight_status_id   = sf.flight_status_id
        INNER JOIN Flight f
               ON f.flight_id           = sf.flight_id
        INNER JOIN Airline al
               ON al.airline_id         = f.airline_id
        INNER JOIN Route r
               ON r.route_id            = f.route_id
        INNER JOIN Airport dep_air
               ON dep_air.airport_id    = r.departs_airport_id
        INNER JOIN Airport arr_air
               ON arr_air.airport_id    = r.arrives_airport_id
        LEFT JOIN FlightOperation fo
               ON fo.schedule_flight_id = sf.schedule_flight_id
              AND fo.flight_operation_status_id NOT IN (
                    SELECT flight_operation_status_id
                    FROM FlightOperationStatus
                    WHERE flight_operation_status_name IN ('Completed', 'Cancelled')
              )
        WHERE fo.schedule_flight_id IS NULL
          AND al.airline_id        = :airline_id
          AND sf.departs_date      > CAST(GETDATE() AS DATE)
          AND sf.departs_date     <= CAST(DATEADD(HOUR, 60, GETDATE()) AS DATE)
          AND fs.flight_status_name = 'Scheduled'
        ORDER BY sf.departs_date ASC
    """)

    rows = db.execute(sql, {"airline_id": airline_id}).mappings().all()
    return rows