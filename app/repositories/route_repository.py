from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from app.models.route_model import Route
    

def get_all(db: Session, airline_id: int | None = None) -> list[Route]:
    query = (
        db.query(Route)
        .options(
            joinedload(Route.departs_airport),
            joinedload(Route.arrives_airport),
        )
    )
    if airline_id is not None:
        query = query.filter(Route.airline_id == airline_id)
    return query.all()


def get_all_airports_with_cities(db: Session) -> list[dict]:
    sql = text("""
        SELECT a.airport_id, a.latitude, a.longitude, c.city_id, c.city_name
        FROM Airport a
        JOIN City c ON a.city_id = c.city_id
    """)
    return db.execute(sql).mappings().all()


def get_all_route_connections(db: Session) -> list[dict]:
    sql = text("""
        SELECT dep_a.city_id AS from_id, arr_a.city_id AS to_id, r.flight_range
        FROM Route r
        JOIN Airport dep_a ON r.departs_airport_id = dep_a.airport_id
        JOIN Airport arr_a ON r.arrives_airport_id = arr_a.airport_id
    """)
    return db.execute(sql).mappings().all()



def hub_has_valid_schedule(
    db: Session,
    from_city_id: int,
    hub_city_id: int,
    to_city_id: int,
) -> bool:
    dates = get_leg1_dates_with_connections(db, from_city_id, hub_city_id, to_city_id)
    return len(dates) > 0


def get_leg2_dates_with_suggestions(
    db: Session,
    from_city_id: int,
    hub_city_id: int,
    to_city_id: int,
    leg1_date: str,
) -> dict:
    """
    Для обраної дати leg1 знаходить:
    - leg2_dates: дати рейсів hub→to_city в межах 24 годин після прильоту leg1
    - suggested_leg1_dates: інші дати leg1 для яких є валідне з'єднання
    """
    sql = text("""
        SELECT
            CAST(f1.departs_datetime AS DATE) AS leg1_date,
            f1.arrives_datetime               AS leg1_arrives,
            f2.departs_datetime               AS leg2_departs,
            CAST(f2.departs_datetime AS DATE) AS leg2_date,
            DATEDIFF(HOUR, f1.arrives_datetime, f2.departs_datetime) AS transfer_hours
        FROM Flight f1
        JOIN FlightSchedule fs1 ON f1.flight_schedule_id = fs1.flight_schedule_id
        JOIN Route r1           ON fs1.route_id = r1.route_id
        JOIN Airport a_dep1     ON r1.departs_airport_id = a_dep1.airport_id
        JOIN Airport a_arr1     ON r1.arrives_airport_id = a_arr1.airport_id

        JOIN Flight f2          ON f2.flight_id != f1.flight_id
        JOIN FlightSchedule fs2 ON f2.flight_schedule_id = fs2.flight_schedule_id
        JOIN Route r2           ON fs2.route_id = r2.route_id
        JOIN Airport a_dep2     ON r2.departs_airport_id = a_dep2.airport_id
        JOIN Airport a_arr2     ON r2.arrives_airport_id = a_arr2.airport_id

        JOIN FlightStatus fs1s  ON f1.flight_status_id = fs1s.flight_status_id
        JOIN FlightStatus fs2s  ON f2.flight_status_id = fs2s.flight_status_id

        WHERE
            a_dep1.city_id = :from_city
            AND a_arr1.city_id = :hub_city
            AND a_dep2.city_id = :hub_city
            AND a_arr2.city_id = :to_city

            AND fs1s.flight_status_name != 'Cancelled'
            AND fs2s.flight_status_name != 'Cancelled'

            AND f1.departs_datetime >= GETDATE()
            AND f2.departs_datetime > f1.arrives_datetime
            AND f2.departs_datetime <= DATEADD(HOUR, 24, f1.arrives_datetime)

            AND (fs1.flight_end_date IS NULL OR fs1.flight_end_date >= GETDATE())
            AND (fs2.flight_end_date IS NULL OR fs2.flight_end_date >= GETDATE())

            AND CAST(f1.departs_datetime AS DATE) >= fs1.flight_start_date
            AND (fs1.flight_end_date IS NULL OR
                 CAST(f1.departs_datetime AS DATE) <= fs1.flight_end_date)
            AND CAST(f2.departs_datetime AS DATE) >= fs2.flight_start_date
            AND (fs2.flight_end_date IS NULL OR
                 CAST(f2.departs_datetime AS DATE) <= fs2.flight_end_date)

        ORDER BY f1.departs_datetime, f2.departs_datetime
    """)

    rows = db.execute(sql, {
        "from_city": from_city_id,
        "hub_city":  hub_city_id,
        "to_city":   to_city_id,
    }).fetchall()

    leg2_dates = set()
    suggested_leg1_dates = set()

    for row in rows:
        row_leg1_date = row.leg1_date.strftime("%Y-%m-%d")
        row_leg2_date = row.leg2_date.strftime("%Y-%m-%d")

        if row_leg1_date == leg1_date:
            leg2_dates.add(row_leg2_date)
        else:
            suggested_leg1_dates.add(row_leg1_date)

    return {
        "leg2_dates": sorted(leg2_dates),
        "suggested_leg1_dates": sorted(suggested_leg1_dates),
    }


def get_leg1_dates_with_connections(
    db: Session,
    from_city_id: int,
    hub_city_id: int,
    to_city_id: int,
) -> list[str]:
    sql = text("""
        SELECT DISTINCT
            CAST(f1.departs_datetime AS DATE) AS leg1_date
        FROM Flight f1
        JOIN FlightSchedule fs1 ON f1.flight_schedule_id = fs1.flight_schedule_id
        JOIN Route r1           ON fs1.route_id = r1.route_id
        JOIN Airport a_dep1     ON r1.departs_airport_id = a_dep1.airport_id
        JOIN Airport a_arr1     ON r1.arrives_airport_id = a_arr1.airport_id

        JOIN Flight f2          ON f2.flight_id != f1.flight_id
        JOIN FlightSchedule fs2 ON f2.flight_schedule_id = fs2.flight_schedule_id
        JOIN Route r2           ON fs2.route_id = r2.route_id
        JOIN Airport a_dep2     ON r2.departs_airport_id = a_dep2.airport_id
        JOIN Airport a_arr2     ON r2.arrives_airport_id = a_arr2.airport_id

        JOIN FlightStatus fs1s  ON f1.flight_status_id = fs1s.flight_status_id
        JOIN FlightStatus fs2s  ON f2.flight_status_id = fs2s.flight_status_id

        WHERE
            a_dep1.city_id = :from_city
            AND a_arr1.city_id = :hub_city
            AND a_dep2.city_id = :hub_city
            AND a_arr2.city_id = :to_city

            AND fs1s.flight_status_name != 'Cancelled'
            AND fs2s.flight_status_name != 'Cancelled'

            AND f1.departs_datetime >= GETDATE()
            AND f2.departs_datetime > f1.arrives_datetime
            AND f2.departs_datetime <= DATEADD(HOUR, 24, f1.arrives_datetime)

            AND (fs1.flight_end_date IS NULL OR fs1.flight_end_date >= GETDATE())
            AND (fs2.flight_end_date IS NULL OR fs2.flight_end_date >= GETDATE())

            AND CAST(f1.departs_datetime AS DATE) >= fs1.flight_start_date
            AND (fs1.flight_end_date IS NULL OR
                 CAST(f1.departs_datetime AS DATE) <= fs1.flight_end_date)
            AND CAST(f2.departs_datetime AS DATE) >= fs2.flight_start_date
            AND (fs2.flight_end_date IS NULL OR
                 CAST(f2.departs_datetime AS DATE) <= fs2.flight_end_date)

        ORDER BY leg1_date
    """)

    rows = db.execute(sql, {
        "from_city": from_city_id,
        "hub_city":  hub_city_id,
        "to_city":   to_city_id,
    }).fetchall()

    return [row.leg1_date.strftime("%Y-%m-%d") for row in rows]


