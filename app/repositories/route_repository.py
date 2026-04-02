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
    sql = text("""
        SELECT TOP 1
            f1.flight_id,
            f1.departs_datetime AS leg1_departs,
            f1.arrives_datetime AS leg1_arrives,
            f2.flight_id        AS f2_id,
            f2.departs_datetime AS leg2_departs,
            DATEDIFF(HOUR, f1.arrives_datetime, f2.departs_datetime) AS transfer_hours
        FROM Flight f1
        JOIN FlightSchedule fs1 ON f1.flight_schedule_id = fs1.flight_schedule_id
        JOIN Route r1           ON fs1.route_id = r1.route_id
        JOIN Airport a_dep1     ON r1.departs_airport_id = a_dep1.airport_id
        JOIN Airport a_arr1     ON r1.arrives_airport_id = a_arr1.airport_id
        JOIN City    c_dep1     ON a_dep1.city_id = c_dep1.city_id
        JOIN City    c_hub      ON a_arr1.city_id = c_hub.city_id

        JOIN Flight f2          ON f2.flight_id != f1.flight_id
        JOIN FlightSchedule fs2 ON f2.flight_schedule_id = fs2.flight_schedule_id
        JOIN Route r2           ON fs2.route_id = r2.route_id
        JOIN Airport a_dep2     ON r2.departs_airport_id = a_dep2.airport_id
        JOIN Airport a_arr2     ON r2.arrives_airport_id = a_arr2.airport_id
        JOIN City    c_arr2     ON a_arr2.city_id = c_arr2.city_id

        WHERE
            c_dep1.city_id = :from_city
            AND a_arr1.city_id = a_dep2.city_id
            AND c_hub.city_id  = :hub_city
            AND c_arr2.city_id = :to_city
            AND (fs1.flight_end_date IS NULL OR fs1.flight_end_date >= GETDATE())
            AND (fs2.flight_end_date IS NULL OR fs2.flight_end_date >= GETDATE())
            AND f1.departs_datetime >= GETDATE()
            AND f2.departs_datetime > f1.arrives_datetime
            AND f2.departs_datetime <= DATEADD(HOUR, 48, f1.arrives_datetime)
            AND CAST(f1.departs_datetime AS DATE) >= fs1.flight_start_date
            AND (fs1.flight_end_date IS NULL OR
                 CAST(f1.departs_datetime AS DATE) <= fs1.flight_end_date)
            AND CAST(f2.departs_datetime AS DATE) >= fs2.flight_start_date
            AND (fs2.flight_end_date IS NULL OR
                 CAST(f2.departs_datetime AS DATE) <= fs2.flight_end_date)
    """)

    row = db.execute(sql, {
        "from_city": from_city_id,
        "hub_city":  hub_city_id,
        "to_city":   to_city_id,
    }).fetchone()

    if row:
        print(f"  hub={hub_city_id} VALID: leg1={row.leg1_departs}→{row.leg1_arrives}, leg2={row.leg2_departs}, transfer={row.transfer_hours}h")
    else:
        print(f"  hub={hub_city_id} INVALID: no valid pair found")

    return row is not None




