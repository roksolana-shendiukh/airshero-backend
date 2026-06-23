from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from app.infrastructure.database.models.flight_model import Flight, Route


def get_all(db: Session, airline_id: int | None = None) -> list[Route]:
    query = (
        db.query(Route)
        .options(
            joinedload(Route.departs_airport),
            joinedload(Route.arrives_airport),
        )
    )
    if airline_id is not None:
        # ✅ airline_id через Flight
        query = (
            query
            .join(Flight, Flight.route_id == Route.route_id)
            .filter(Flight.airline_id == airline_id)
        )
    return query.all()


def get_all_airports_with_cities(db: Session) -> list[dict]:
    sql = text("""
        SELECT a.airport_id, a.latitude, a.longitude,
               c.city_id, c.city_name
        FROM Airport a
        JOIN City c ON c.city_id = a.city_id
    """)
    return db.execute(sql).mappings().all()


def get_all_route_connections(db: Session) -> list[dict]:
    sql = text("""
        SELECT dep_a.city_id AS from_id,
               arr_a.city_id AS to_id,
               r.flight_range
        FROM Route r
        JOIN Airport dep_a ON dep_a.airport_id = r.departs_airport_id
        JOIN Airport arr_a ON arr_a.airport_id = r.arrives_airport_id
    """)
    return db.execute(sql).mappings().all()


def hub_has_valid_schedule(
    db: Session,
    from_city_id: int,
    hub_city_id: int,
    to_city_id: int,
) -> bool:
    dates = get_leg1_dates_with_connections(
        db, from_city_id, hub_city_id, to_city_id
    )
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
    - leg2_dates: дати рейсів hub→to_city в межах 24 годин після вильоту leg1
    - suggested_leg1_dates: інші дати leg1 для яких є валідне з'єднання

    Оскільки точного часу прильоту немає — використовуємо
    schedule_departure_time + flight_duration як апроксимацію часу прильоту.
    """
    sql = text("""
        SELECT
            sf1.departs_date                         AS leg1_date,
            -- апроксимація прильоту leg1:
            -- departs_date + departure_time + flight_duration
            DATEADD(
                MINUTE,
                DATEDIFF(MINUTE, 0, f1.flight_duration),
                CAST(
                    CAST(sf1.departs_date AS DATETIME)
                    + CAST(s1.schedule_departure_time AS DATETIME)
                AS DATETIME)
            )                                        AS leg1_arrives,
            CAST(
                CAST(sf2.departs_date AS DATETIME)
                + CAST(s2.schedule_departure_time AS DATETIME)
            AS DATETIME)                             AS leg2_departs,
            sf2.departs_date                         AS leg2_date,
            DATEDIFF(
                HOUR,
                DATEADD(
                    MINUTE,
                    DATEDIFF(MINUTE, 0, f1.flight_duration),
                    CAST(
                        CAST(sf1.departs_date AS DATETIME)
                        + CAST(s1.schedule_departure_time AS DATETIME)
                    AS DATETIME)
                ),
                CAST(
                    CAST(sf2.departs_date AS DATETIME)
                    + CAST(s2.schedule_departure_time AS DATETIME)
                AS DATETIME)
            )                                        AS transfer_hours
        FROM ScheduledFlight sf1
        INNER JOIN FlightStatus fss1
               ON fss1.flight_status_id   = sf1.flight_status_id
              AND fss1.flight_status_name != 'Cancelled'
        INNER JOIN Flight f1     ON f1.flight_id          = sf1.flight_id
        INNER JOIN Route r1      ON r1.route_id            = f1.route_id
        INNER JOIN Airport a_dep1 ON a_dep1.airport_id    = r1.departs_airport_id
        INNER JOIN Airport a_arr1 ON a_arr1.airport_id    = r1.arrives_airport_id
        -- час вильоту leg1
        LEFT JOIN FlightSchedule fsch1
               ON fsch1.flight_id         = f1.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds1
               ON fsds1.flight_schedule_id = fsch1.flight_schedule_id
        LEFT JOIN DaySchedule ds1
               ON ds1.day_schedule_id     = fsds1.day_schedule_id
              AND ds1.day_id = (
                    SELECT TOP 1 d_inner.day_id
                    FROM DayForSchedule d_inner
                    WHERE d_inner.day_name = DATENAME(WEEKDAY, sf1.departs_date)
              )
        LEFT JOIN Schedule s1    ON s1.schedule_id        = ds1.schedule_id

        INNER JOIN ScheduledFlight sf2
               ON sf2.flight_id != sf1.flight_id
        INNER JOIN FlightStatus fss2
               ON fss2.flight_status_id   = sf2.flight_status_id
              AND fss2.flight_status_name != 'Cancelled'
        INNER JOIN Flight f2     ON f2.flight_id          = sf2.flight_id
        INNER JOIN Route r2      ON r2.route_id            = f2.route_id
        INNER JOIN Airport a_dep2 ON a_dep2.airport_id    = r2.departs_airport_id
        INNER JOIN Airport a_arr2 ON a_arr2.airport_id    = r2.arrives_airport_id
        -- час вильоту leg2
        LEFT JOIN FlightSchedule fsch2
               ON fsch2.flight_id         = f2.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds2
               ON fsds2.flight_schedule_id = fsch2.flight_schedule_id
        LEFT JOIN DaySchedule ds2
               ON ds2.day_schedule_id     = fsds2.day_schedule_id
              AND ds2.day_id = (
                    SELECT TOP 1 d_inner.day_id
                    FROM DayForSchedule d_inner
                    WHERE d_inner.day_name = DATENAME(WEEKDAY, sf2.departs_date)
              )
        LEFT JOIN Schedule s2    ON s2.schedule_id        = ds2.schedule_id

        WHERE
            a_dep1.city_id = :from_city
            AND a_arr1.city_id = :hub_city
            AND a_dep2.city_id = :hub_city
            AND a_arr2.city_id = :to_city
            AND sf1.departs_date >= CAST(GETDATE() AS DATE)
            -- leg2 вилітає після прильоту leg1 і не пізніше ніж через 24 год
            AND CAST(sf2.departs_date AS DATETIME)
                + CAST(s2.schedule_departure_time AS DATETIME)
                > DATEADD(
                    MINUTE,
                    DATEDIFF(MINUTE, 0, f1.flight_duration),
                    CAST(sf1.departs_date AS DATETIME)
                    + CAST(s1.schedule_departure_time AS DATETIME)
                  )
            AND CAST(sf2.departs_date AS DATETIME)
                + CAST(s2.schedule_departure_time AS DATETIME)
                <= DATEADD(
                    HOUR, 24,
                    DATEADD(
                        MINUTE,
                        DATEDIFF(MINUTE, 0, f1.flight_duration),
                        CAST(sf1.departs_date AS DATETIME)
                        + CAST(s1.schedule_departure_time AS DATETIME)
                    )
                )
        ORDER BY sf1.departs_date, s1.schedule_departure_time,
                 sf2.departs_date, s2.schedule_departure_time
    """)

    rows = db.execute(sql, {
        "from_city": from_city_id,
        "hub_city":  hub_city_id,
        "to_city":   to_city_id,
    }).fetchall()

    leg2_dates          = set()
    suggested_leg1_dates = set()

    for row in rows:
        row_leg1 = str(row.leg1_date)
        row_leg2 = str(row.leg2_date)
        if row_leg1 == leg1_date:
            leg2_dates.add(row_leg2)
        else:
            suggested_leg1_dates.add(row_leg1)

    return {
        "leg2_dates":            sorted(leg2_dates),
        "suggested_leg1_dates":  sorted(suggested_leg1_dates),
    }


def get_leg1_dates_with_connections(
    db: Session,
    from_city_id: int,
    hub_city_id: int,
    to_city_id: int,
) -> list[str]:
    sql = text("""
        SELECT DISTINCT sf1.departs_date AS leg1_date
        FROM ScheduledFlight sf1
        INNER JOIN FlightStatus fss1
               ON fss1.flight_status_id   = sf1.flight_status_id
              AND fss1.flight_status_name != 'Cancelled'
        INNER JOIN Flight f1      ON f1.flight_id         = sf1.flight_id
        INNER JOIN Route r1       ON r1.route_id           = f1.route_id
        INNER JOIN Airport a_dep1 ON a_dep1.airport_id    = r1.departs_airport_id
        INNER JOIN Airport a_arr1 ON a_arr1.airport_id    = r1.arrives_airport_id
        LEFT JOIN FlightSchedule fsch1
               ON fsch1.flight_id         = f1.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds1
               ON fsds1.flight_schedule_id = fsch1.flight_schedule_id
        LEFT JOIN DaySchedule ds1
               ON ds1.day_schedule_id     = fsds1.day_schedule_id
              AND ds1.day_id = (
                    SELECT TOP 1 d_inner.day_id
                    FROM DayForSchedule d_inner
                    WHERE d_inner.day_name = DATENAME(WEEKDAY, sf1.departs_date)
              )
        LEFT JOIN Schedule s1     ON s1.schedule_id       = ds1.schedule_id

        INNER JOIN ScheduledFlight sf2
               ON sf2.flight_id != sf1.flight_id
        INNER JOIN FlightStatus fss2
               ON fss2.flight_status_id   = sf2.flight_status_id
              AND fss2.flight_status_name != 'Cancelled'
        INNER JOIN Flight f2      ON f2.flight_id         = sf2.flight_id
        INNER JOIN Route r2       ON r2.route_id           = f2.route_id
        INNER JOIN Airport a_dep2 ON a_dep2.airport_id    = r2.departs_airport_id
        INNER JOIN Airport a_arr2 ON a_arr2.airport_id    = r2.arrives_airport_id
        LEFT JOIN FlightSchedule fsch2
               ON fsch2.flight_id         = f2.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds2
               ON fsds2.flight_schedule_id = fsch2.flight_schedule_id
        LEFT JOIN DaySchedule ds2
               ON ds2.day_schedule_id     = fsds2.day_schedule_id
              AND ds2.day_id = (
                    SELECT TOP 1 d_inner.day_id
                    FROM DayForSchedule d_inner
                    WHERE d_inner.day_name = DATENAME(WEEKDAY, sf2.departs_date)
              )
        LEFT JOIN Schedule s2     ON s2.schedule_id       = ds2.schedule_id

        WHERE
            a_dep1.city_id = :from_city
            AND a_arr1.city_id = :hub_city
            AND a_dep2.city_id = :hub_city
            AND a_arr2.city_id = :to_city
            AND sf1.departs_date >= CAST(GETDATE() AS DATE)
            AND CAST(sf2.departs_date AS DATETIME)
                + CAST(s2.schedule_departure_time AS DATETIME)
                > DATEADD(
                    MINUTE,
                    DATEDIFF(MINUTE, 0, f1.flight_duration),
                    CAST(sf1.departs_date AS DATETIME)
                    + CAST(s1.schedule_departure_time AS DATETIME)
                  )
            AND CAST(sf2.departs_date AS DATETIME)
                + CAST(s2.schedule_departure_time AS DATETIME)
                <= DATEADD(
                    HOUR, 24,
                    DATEADD(
                        MINUTE,
                        DATEDIFF(MINUTE, 0, f1.flight_duration),
                        CAST(sf1.departs_date AS DATETIME)
                        + CAST(s1.schedule_departure_time AS DATETIME)
                    )
                )
        ORDER BY leg1_date
    """)

    rows = db.execute(sql, {
        "from_city": from_city_id,
        "hub_city":  hub_city_id,
        "to_city":   to_city_id,
    }).fetchall()

    return [str(row.leg1_date) for row in rows]