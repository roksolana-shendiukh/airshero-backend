from sqlalchemy.orm import Session
from sqlalchemy import text


def search_flights(db: Session, from_city: int, to_city: int, depart_date: str):
    result = db.execute(
        text("EXEC SP_SearchFlights :departs_city_id, :arrives_city_id, :departs_date"),
        {
            "departs_city_id": from_city,
            "arrives_city_id": to_city,
            "departs_date": depart_date,
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

    conditions = [f"f.flight_id IN ({flight_placeholders})"]

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

    slot_map = {
        "night":     "(DATEPART(HOUR, f.departs_datetime) >= 0  AND DATEPART(HOUR, f.departs_datetime) < 6)",
        "morning":   "(DATEPART(HOUR, f.departs_datetime) >= 6  AND DATEPART(HOUR, f.departs_datetime) < 12)",
        "afternoon": "(DATEPART(HOUR, f.departs_datetime) >= 12 AND DATEPART(HOUR, f.departs_datetime) < 18)",
        "evening":   "(DATEPART(HOUR, f.departs_datetime) >= 18 AND DATEPART(HOUR, f.departs_datetime) < 24)",
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
            fc.flight_class_id,
            fp.flight_price_id,
            r.flight_number,
            dep_air.airport_name AS departure_airport_name,
            dep_air.airport_code AS departure_airport_code,
            arr_air.airport_name AS arrival_airport_name,
            arr_air.airport_code AS arrival_airport_code,
            f.departs_datetime,
            f.arrives_datetime,
            CONVERT(VARCHAR(5), r.flight_duration, 108) AS flight_duration,
            c.class_name,
            fp.ticket_price,
            fs.flight_status_name,
            al.airline_name,
            al.airline_url AS airline_logo_url
        FROM Flight f
        INNER JOIN FlightSchedule fsched ON f.flight_schedule_id = fsched.flight_schedule_id
        INNER JOIN Route r ON fsched.route_id = r.route_id
        INNER JOIN Airline al ON r.airline_id = al.airline_id
        INNER JOIN Airport dep_air ON r.departs_airport_id = dep_air.airport_id
        INNER JOIN Airport arr_air ON r.arrives_airport_id = arr_air.airport_id
        INNER JOIN FlightStatus fs ON f.flight_status_id = fs.flight_status_id
        INNER JOIN FlightClass fc ON f.flight_id = fc.flight_id
        INNER JOIN Class c ON fc.class_id = c.class_id
        INNER JOIN FlightPrice fp ON fc.flight_class_id = fp.flight_class_id
            AND fp.flight_published_date = (
                SELECT MAX(fp2.flight_published_date)
                FROM FlightPrice fp2
                WHERE fp2.flight_class_id = fc.flight_class_id
            )
        WHERE {where}
        ORDER BY {order}, f.departs_datetime ASC
    """)

    result = db.execute(sql, params)
    return result.mappings().all()


def get_flights_without_operation(db: Session, airline_id: int):
    sql = text("""
    SELECT
        f.flight_id,
        r.flight_number,
        dep_air.airport_id   AS departs_airport_id,
        dep_air.airport_code AS departs_code,
        arr_air.airport_code AS arrives_code,
        f.departs_datetime,
        f.arrives_datetime,
        fs.flight_status_name,
        al.airline_name AS airline_name
    FROM Flight f
    INNER JOIN FlightSchedule fsched ON f.flight_schedule_id = fsched.flight_schedule_id
    INNER JOIN Route r ON fsched.route_id = r.route_id
    INNER JOIN Airline al ON r.airline_id = al.airline_id
    INNER JOIN Airport dep_air ON r.departs_airport_id = dep_air.airport_id
    INNER JOIN Airport arr_air ON r.arrives_airport_id = arr_air.airport_id
    INNER JOIN FlightStatus fs ON f.flight_status_id = fs.flight_status_id
    LEFT JOIN FlightOperation fo ON f.flight_id = fo.flight_id
        AND fo.flight_operation_status_id NOT IN (
            SELECT flight_operation_status_id 
            FROM FlightOperationStatus 
            WHERE flight_operation_status_name IN ('Completed', 'Cancelled')
        )
    WHERE fo.flight_id IS NULL
      AND al.airline_id = :airline_id
      AND f.departs_datetime > GETDATE()
      AND f.departs_datetime <= DATEADD(HOUR, 60, GETDATE())
      AND fs.flight_status_name = 'Scheduled'
    ORDER BY f.departs_datetime ASC
    """)

    print(f">>> get_flights_without_operation airline_id={airline_id}")
    rows = db.execute(sql, {"airline_id": airline_id}).mappings().all()
    print(f">>> rows count: {len(rows)}")
    return rows

