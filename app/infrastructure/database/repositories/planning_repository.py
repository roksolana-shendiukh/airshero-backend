from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, timedelta, datetime
import random


def get_overview_flights(
    db: Session,
    airline_id: int,
    mode: str = "day",
    date: str | None = None,
    month: int | None = None,
    year: int | None = None,
    status: str | None = None,
    flight_number: str | None = None,
):
    conditions = ["f.airline_id = :airline_id"]
    params: dict = {"airline_id": airline_id}

    if mode == "day" and date:
        conditions.append("sf.departs_date = :date")
        params["date"] = date
    elif mode == "month" and month and year:
        conditions.append("MONTH(sf.departs_date) = :month")
        conditions.append("YEAR(sf.departs_date) = :year")
        params["month"] = month
        params["year"] = year

    if status:
        conditions.append("fs.flight_status_name = :status")
        params["status"] = status

    if flight_number:
        conditions.append("f.flight_number LIKE :flight_number")
        params["flight_number"] = f"%{flight_number}%"

    where = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            f.flight_id,
            sf.schedule_flight_id,
            f.flight_number,
            dep_air.airport_code        AS departs_code,
            arr_air.airport_code        AS arrives_code,
            sf.departs_date,
            s.schedule_departure_time,
            s.schedule_arrival_time,
            CONVERT(VARCHAR(5), f.flight_duration, 108) AS flight_duration,
            fs.flight_status_name,
            af.aircraft_model,
            af.seat_capacity,
            (
                SELECT STRING_AGG(c_sub.class_name, ', ')
                       WITHIN GROUP (ORDER BY c_sub.class_name)
                FROM FlightClass fc_sub
                JOIN Class c_sub ON fc_sub.class_id = c_sub.class_id
                WHERE fc_sub.flight_id = f.flight_id
            ) AS classes,
            COUNT(DISTINCT bi.booking_item_id) AS booked_seats
        FROM ScheduledFlight sf
        INNER JOIN FlightStatus fs   ON fs.flight_status_id  = sf.flight_status_id
        INNER JOIN Flight f          ON f.flight_id           = sf.flight_id
        INNER JOIN Airline al        ON al.airline_id         = f.airline_id
        INNER JOIN Airfleet af       ON af.airfleet_id        = f.airfleet_id
        INNER JOIN Route r           ON r.route_id            = f.route_id
        INNER JOIN Airport dep_air   ON dep_air.airport_id    = r.departs_airport_id
        INNER JOIN Airport arr_air   ON arr_air.airport_id    = r.arrives_airport_id
        -- час через FlightSchedule → FlightScheduleDaySchedule → DaySchedule → Schedule
        LEFT JOIN FlightSchedule fsch
               ON fsch.flight_id     = f.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds
               ON fsds.flight_schedule_id = fsch.flight_schedule_id
        LEFT JOIN DaySchedule ds     ON ds.day_schedule_id   = fsds.day_schedule_id
        LEFT JOIN Schedule s         ON s.schedule_id        = ds.schedule_id
        LEFT JOIN FlightClass fc     ON fc.flight_id         = f.flight_id
        LEFT JOIN FlightPrice fp
               ON fp.flight_class_id    = fc.flight_class_id
              AND fp.schedule_flight_id = sf.schedule_flight_id
              AND fp.flight_published_date = (
                    SELECT MAX(fp2.flight_published_date)
                    FROM FlightPrice fp2
                    WHERE fp2.flight_class_id    = fc.flight_class_id
                      AND fp2.schedule_flight_id = sf.schedule_flight_id
              )
        LEFT JOIN BookingItem bi     ON bi.flight_price_id   = fp.flight_price_id
        LEFT JOIN Booking b          ON b.booking_id         = bi.booking_id
        LEFT JOIN BookingStatus bs
               ON bs.booking_status_id = b.booking_status_id
              AND bs.booking_status_name IN ('Confirmed', 'Completed')
        WHERE {where}
        GROUP BY
            f.flight_id, sf.schedule_flight_id,
            f.flight_number,
            dep_air.airport_code, arr_air.airport_code,
            sf.departs_date,
            s.schedule_departure_time, s.schedule_arrival_time,
            f.flight_duration, fs.flight_status_name,
            af.aircraft_model, af.seat_capacity
        ORDER BY sf.departs_date ASC, s.schedule_departure_time ASC
    """)

    return db.execute(sql, params).mappings().all()


def get_overview_stats(db: Session, airline_id: int):
    sql = text("""
        WITH FlightBase AS (
            SELECT
                sf.schedule_flight_id,
                sf.flight_id,
                af.seat_capacity,
                fs.flight_status_name,
                f.route_id
            FROM ScheduledFlight sf
            INNER JOIN FlightStatus fs ON fs.flight_status_id = sf.flight_status_id
            INNER JOIN Flight f        ON f.flight_id         = sf.flight_id
            INNER JOIN Airfleet af     ON af.airfleet_id      = f.airfleet_id
            WHERE f.airline_id = :airline_id
        ),
        ActiveFlights AS (
            SELECT schedule_flight_id, flight_id, seat_capacity, route_id
            FROM FlightBase
            WHERE flight_status_name IN ('Scheduled', 'Boarding', 'Departed')
        ),
        BookedSeats AS (
            SELECT
                fp.schedule_flight_id,
                COUNT(DISTINCT bi.booking_item_id) AS booked_count
            FROM FlightClass fc
            INNER JOIN FlightPrice fp
                   ON fp.flight_class_id    = fc.flight_class_id
                  AND fp.schedule_flight_id IN (
                        SELECT schedule_flight_id FROM ActiveFlights)
                  AND fp.flight_published_date = (
                        SELECT MAX(fp2.flight_published_date)
                        FROM FlightPrice fp2
                        WHERE fp2.flight_class_id    = fc.flight_class_id
                          AND fp2.schedule_flight_id = fp.schedule_flight_id
                  )
            INNER JOIN BookingItem bi  ON bi.flight_price_id  = fp.flight_price_id
            INNER JOIN Booking b       ON b.booking_id        = bi.booking_id
            INNER JOIN BookingStatus bs
                   ON bs.booking_status_id   = b.booking_status_id
                  AND bs.booking_status_name IN ('Confirmed', 'Completed')
            WHERE fc.flight_id IN (SELECT flight_id FROM ActiveFlights)
            GROUP BY fp.schedule_flight_id
        ),
        MonthlyRevenue AS (
            SELECT COALESCE(SUM(p.payment_amount), 0) AS revenue
            FROM Payment p
            INNER JOIN PaymentStatus ps
                   ON ps.payment_status_id   = p.payment_status_id
                  AND ps.payment_status_name = 'Completed'
            INNER JOIN Booking b       ON b.booking_id        = p.booking_id
            INNER JOIN BookingItem bi  ON bi.booking_id       = b.booking_id
            INNER JOIN FlightPrice fp  ON fp.flight_price_id  = bi.flight_price_id
            INNER JOIN FlightClass fc  ON fc.flight_class_id  = fp.flight_class_id
            INNER JOIN Flight f        ON f.flight_id         = fc.flight_id
            WHERE f.airline_id = :airline_id
              AND MONTH(p.payment_date_time) = MONTH(GETDATE())
              AND YEAR(p.payment_date_time)  = YEAR(GETDATE())
        )
        SELECT
            (SELECT COUNT(*)               FROM ActiveFlights) AS active_flights_count,
            (SELECT COUNT(DISTINCT route_id) FROM ActiveFlights) AS routes_count,
            (
                SELECT COALESCE(AVG(
                    CAST(bs.booked_count AS FLOAT) /
                    NULLIF(af.seat_capacity, 0) * 100
                ), 0)
                FROM ActiveFlights af
                LEFT JOIN BookedSeats bs
                       ON bs.schedule_flight_id = af.schedule_flight_id
            ) AS average_load_percent,
            (SELECT revenue FROM MonthlyRevenue) AS monthly_revenue_eur
    """)

    return db.execute(sql, {"airline_id": airline_id}).mappings().one()


def get_available_dates(db: Session, airline_id: int) -> list[str]:
    sql = text("""
        SELECT DISTINCT sf.departs_date AS flight_date
        FROM ScheduledFlight sf
        INNER JOIN Flight f ON f.flight_id = sf.flight_id
        WHERE f.airline_id = :airline_id
        ORDER BY flight_date ASC
    """)
    return [
        str(row["flight_date"])
        for row in db.execute(sql, {"airline_id": airline_id}).mappings().all()
    ]


def get_booked_dates_for_schedule(db: Session, flight_schedule_id: int) -> list[str]:
    sql = text("""
        SELECT DISTINCT sf.departs_date AS flight_date
        FROM ScheduledFlight sf
        INNER JOIN Flight f         ON f.flight_id          = sf.flight_id
        INNER JOIN FlightSchedule fsch
               ON fsch.flight_id   = f.flight_id
        WHERE fsch.flight_schedule_id = :flight_schedule_id
        ORDER BY flight_date ASC
    """)
    return [
        str(row["flight_date"])
        for row in db.execute(
            sql, {"flight_schedule_id": flight_schedule_id}
        ).mappings().all()
    ]


def get_available_months(db: Session, airline_id: int) -> list[str]:
    sql = text("""
        SELECT DISTINCT
            YEAR(sf.departs_date)  AS yr,
            MONTH(sf.departs_date) AS mo
        FROM ScheduledFlight sf
        INNER JOIN Flight f ON f.flight_id = sf.flight_id
        WHERE f.airline_id = :airline_id
        ORDER BY yr, mo
    """)
    return [
        f"{row['yr']}-{str(row['mo']).zfill(2)}"
        for row in db.execute(sql, {"airline_id": airline_id}).mappings().all()
    ]


def get_routes_for_airline(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT
            r.route_id,
            f.flight_number,
            f.airfleet_id,
            af.aircraft_model,
            af.seat_capacity,
            dep.airport_code AS departs_code,
            dep.airport_name AS departs_airport,
            arr.airport_code AS arrives_code,
            arr.airport_name AS arrives_airport,
            CONVERT(VARCHAR(5), f.flight_duration, 108) AS flight_duration
        FROM Route r
        INNER JOIN Flight f    ON f.route_id          = r.route_id
        INNER JOIN Airfleet af ON af.airfleet_id      = f.airfleet_id
        INNER JOIN Airport dep ON dep.airport_id      = r.departs_airport_id
        INNER JOIN Airport arr ON arr.airport_id      = r.arrives_airport_id
        WHERE f.airline_id = :airline_id
        ORDER BY f.flight_number
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def get_route_schedules(db: Session, route_id: int) -> list:
    sql = text("""
        SELECT
            fsch.flight_schedule_id,
            fsn.season_start_date,
            fsn.season_end_date,
            ds.day_id,
            d.day_name,
            s.schedule_departure_time,
            s.schedule_arrival_time
        FROM FlightSchedule fsch
        INNER JOIN FlightSeason fsn
               ON fsn.flight_season_id       = fsch.flight_season_id
        INNER JOIN FlightScheduleDaySchedule fsds
               ON fsds.flight_schedule_id    = fsch.flight_schedule_id
        INNER JOIN DaySchedule ds
               ON ds.day_schedule_id         = fsds.day_schedule_id
        INNER JOIN Schedule s
               ON s.schedule_id              = ds.schedule_id
        INNER JOIN DayForSchedule d
               ON d.day_id                   = ds.day_id
        INNER JOIN Flight f
               ON f.flight_id                = fsch.flight_id
        WHERE f.route_id = :route_id
        ORDER BY fsch.flight_schedule_id, ds.day_id
    """)
    return db.execute(sql, {"route_id": route_id}).mappings().all()


def get_seat_layout_for_airfleet(db: Session, airfleet_id: int) -> list:
    sql = text("""
        SELECT
            sl.seat_layout_id,
            sl.seat_layout_rows,
            sl.seat_layout_columns,
            c.class_id,
            c.class_name,
            st.seat_type_name
        FROM SeatLayout sl
        INNER JOIN Class c    ON c.class_id       = sl.class_id
        INNER JOIN SeatType st ON st.seat_type_id = sl.seat_type_id
        WHERE sl.airfleet_id = :airfleet_id
        ORDER BY sl.seat_layout_rows, sl.seat_layout_columns
    """)
    return db.execute(sql, {"airfleet_id": airfleet_id}).mappings().all()


def get_status_id_by_name(db: Session, status_name: str) -> int:
    sql = text("""
        SELECT flight_status_id
        FROM FlightStatus
        WHERE flight_status_name = :status_name
    """)
    return db.execute(sql, {"status_name": status_name}).scalar()


def create_flight(
    db: Session,
    flight_id: int,
    flight_status_id: int,
    departs_date: str,
    class_prices: list[dict],
) -> int:
    # Створюємо ScheduledFlight (саме тут живе статус і дата)
    sql_sf = text("""
        INSERT INTO ScheduledFlight
            (flight_id, flight_status_id, departs_date, sales_start_date)
        OUTPUT INSERTED.schedule_flight_id
        VALUES (:flight_id, :flight_status_id, :departs_date, CAST(GETDATE() AS DATE))
    """)
    schedule_flight_id = db.execute(sql_sf, {
        "flight_id":        flight_id,
        "flight_status_id": flight_status_id,
        "departs_date":     departs_date,
    }).scalar()

    for cp in class_prices:
        sql_fc = text("""
            INSERT INTO FlightClass (class_id, flight_id)
            OUTPUT INSERTED.flight_class_id
            VALUES (:class_id, :flight_id)
        """)
        flight_class_id = db.execute(sql_fc, {
            "class_id":  cp["class_id"],
            "flight_id": flight_id,
        }).scalar()

        db.execute(text("""
            INSERT INTO FlightPrice
                (schedule_flight_id, flight_class_id,
                 flight_published_date, ticket_price)
            VALUES
                (:schedule_flight_id, :flight_class_id,
                 CAST(GETDATE() AS DATE), :ticket_price)
        """), {
            "schedule_flight_id": schedule_flight_id,
            "flight_class_id":    flight_class_id,
            "ticket_price":       cp["price"],
        })

    db.flush()
    return schedule_flight_id


def get_all_baggage_rules(db: Session) -> list:
    sql = text("""
        SELECT
            bpr.baggage_pricing_rule_id,
            bt.baggage_type_id,
            bt.baggage_type_name,
            bpr.baggage_dimension,
            bpr.baggage_max_weight,
            bpr.overweight_fee_per_kg
        FROM BaggagePricingRule bpr
        INNER JOIN BaggageType bt ON bt.baggage_type_id = bpr.baggage_type_id
        ORDER BY bt.baggage_type_id, bpr.baggage_max_weight
    """)
    return db.execute(sql).mappings().all()


def add_baggage_to_flight(db: Session, flight_id: int, baggage_options: list[dict]):
    flight_classes = db.execute(text("""
        SELECT class_id, flight_class_id
        FROM FlightClass
        WHERE flight_id = :flight_id
    """), {"flight_id": flight_id}).mappings().all()

    class_map = {row["class_id"]: row["flight_class_id"] for row in flight_classes}

    for opt in baggage_options:
        flight_class_id = class_map.get(opt["class_id"])
        if flight_class_id:
            db.execute(text("""
                INSERT INTO BaggagePricingInFlight
                    (flight_id, baggage_pricing_rule_id,
                     flight_class_id, baggage_price)
                VALUES
                    (:flight_id, :rule_id, :flight_class_id, :price)
            """), {
                "flight_id":       flight_id,
                "rule_id":         opt["baggage_pricing_rule_id"],
                "flight_class_id": flight_class_id,
                "price":           opt["price"],
            })

    db.flush()


def get_airfleets_for_airline(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT
            af.airfleet_id,
            af.aircraft_model,
            af.seat_capacity,
            af.aircraft_range_km,
            af.aircraft_speed,
            af.baggage_capacity,
            m.airfleet_manufacturer_name
        FROM Airfleet af
        INNER JOIN AirlineAirfleet aa
               ON aa.airfleet_id = af.airfleet_id
        INNER JOIN AirfleetManufacturer m
               ON m.airfleet_manufacturer_id = af.airfleet_manufacturer_id
        WHERE aa.airline_id = :airline_id
        ORDER BY af.aircraft_model
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def get_airports_for_airline(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT DISTINCT
            a.airport_id,
            a.airport_name,
            a.airport_code,
            c.city_name,
            co.country_name
        FROM Airport a
        INNER JOIN City c       ON c.city_id      = a.city_id
        INNER JOIN Country co   ON co.country_id  = c.country_id
        INNER JOIN Route r      ON r.departs_airport_id = a.airport_id
                                OR r.arrives_airport_id = a.airport_id
        INNER JOIN Flight f     ON f.route_id     = r.route_id
        WHERE f.airline_id = :airline_id
        ORDER BY a.airport_code
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def check_flight_number_exists(db: Session, flight_number: str) -> bool:
    count = db.execute(text("""
        SELECT COUNT(*) FROM Flight WHERE flight_number = :flight_number
    """), {"flight_number": flight_number}).scalar()
    return count > 0


def calculate_route_range_and_duration(
    db: Session,
    departs_airport_id: int,
    arrives_airport_id: int,
    airfleet_id: int,
) -> dict:
    import math
    row = db.execute(text("""
        SELECT
            dep.latitude  AS dep_lat,
            dep.longitude AS dep_lon,
            arr.latitude  AS arr_lat,
            arr.longitude AS arr_lon,
            af.aircraft_speed
        FROM Airport dep, Airport arr, Airfleet af
        WHERE dep.airport_id = :dep_id
          AND arr.airport_id = :arr_id
          AND af.airfleet_id = :airfleet_id
    """), {
        "dep_id":      departs_airport_id,
        "arr_id":      arrives_airport_id,
        "airfleet_id": airfleet_id,
    }).mappings().one()

    lat1 = math.radians(float(row["dep_lat"]))
    lon1 = math.radians(float(row["dep_lon"]))
    lat2 = math.radians(float(row["arr_lat"]))
    lon2 = math.radians(float(row["arr_lon"]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    range_km = round(6371 * 2 * math.asin(math.sqrt(a)), 2)

    speed = float(row["aircraft_speed"]) if row["aircraft_speed"] else 850.0
    total_minutes = int(round(range_km / speed * 60))
    duration_str = f"{total_minutes // 60:02d}:{total_minutes % 60:02d}:00"

    return {"range_km": range_km, "duration": duration_str}


def create_route(
    db: Session,
    airline_id: int,
    airfleet_id: int,
    departs_airport_id: int,
    arrives_airport_id: int,
    flight_number: str,
    flight_range: float,
    flight_duration: str,
) -> int:
    # Route зберігає тільки аеропорти і дальність
    route_id = db.execute(text("""
        INSERT INTO Route (departs_airport_id, arrives_airport_id, flight_range)
        OUTPUT INSERTED.route_id
        VALUES (:departs_airport_id, :arrives_airport_id, :flight_range)
    """), {
        "departs_airport_id": departs_airport_id,
        "arrives_airport_id": arrives_airport_id,
        "flight_range":       flight_range,
    }).scalar()

    # Flight зберігає airline, airfleet, номер рейсу, тривалість
    db.execute(text("""
        INSERT INTO Flight
            (airline_id, airfleet_id, route_id,
             flight_number, flight_duration, is_deleted)
        VALUES
            (:airline_id, :airfleet_id, :route_id,
             :flight_number, :flight_duration, 0)
    """), {
        "airline_id":      airline_id,
        "airfleet_id":     airfleet_id,
        "route_id":        route_id,
        "flight_number":   flight_number,
        "flight_duration": flight_duration,
    })

    db.flush()
    return route_id


def create_schedule_for_route(
    db: Session,
    flight_id: int,
    flight_season_id: int,
    schedule_groups: list[dict],
) -> int:
    flight_schedule_id = db.execute(text("""
        INSERT INTO FlightSchedule (flight_id, flight_season_id)
        OUTPUT INSERTED.flight_schedule_id
        VALUES (:flight_id, :flight_season_id)
    """), {
        "flight_id":        flight_id,
        "flight_season_id": flight_season_id,
    }).scalar()

    for group in schedule_groups:
        dep_time = group["departure_time"]
        dep_dt   = datetime.strptime(dep_time, "%H:%M")
        arr_time = (dep_dt + timedelta(
            hours=int(group.get("duration_hours", 0)),
            minutes=int(group.get("duration_minutes", 0)),
        )).strftime("%H:%M")

        schedule_id = db.execute(text("""
            INSERT INTO Schedule (schedule_departure_time, schedule_arrival_time)
            OUTPUT INSERTED.schedule_id
            VALUES (:dep_time, :arr_time)
        """), {"dep_time": dep_time, "arr_time": arr_time}).scalar()

        for day_id in group["day_ids"]:
            day_schedule_id = db.execute(text("""
                INSERT INTO DaySchedule (schedule_id, day_id)
                OUTPUT INSERTED.day_schedule_id
                VALUES (:schedule_id, :day_id)
            """), {"schedule_id": schedule_id, "day_id": day_id}).scalar()

            db.execute(text("""
                INSERT INTO FlightScheduleDaySchedule
                    (flight_schedule_id, day_schedule_id)
                VALUES (:flight_schedule_id, :day_schedule_id)
            """), {
                "flight_schedule_id": flight_schedule_id,
                "day_schedule_id":    day_schedule_id,
            })

    db.flush()
    return flight_schedule_id


def generate_flights_for_schedule(
    db: Session,
    flight_id: int,
    flight_season_id: int,
    schedule_groups: list[dict],
    flight_status_id: int,
) -> int:
    season = db.execute(text("""
        SELECT season_start_date, season_end_date
        FROM FlightSeason WHERE flight_season_id = :id
    """), {"id": flight_season_id}).mappings().one()

    start = season["season_start_date"]
    end   = season["season_end_date"]

    source_sf_id = get_last_configured_scheduled_flight(db, flight_id)

    day_map = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6}
    count = 0

    for group in schedule_groups:
        weekdays = {day_map[d] for d in group["day_ids"]}
        current  = start

        while current <= end:
            if current.weekday() in weekdays:
                sf_id = db.execute(text("""
                    INSERT INTO ScheduledFlight
                        (flight_id, flight_status_id,
                         departs_date, sales_start_date)
                    OUTPUT INSERTED.schedule_flight_id
                    VALUES (:flight_id, :status_id,
                            :departs_date, CAST(GETDATE() AS DATE))
                """), {
                    "flight_id":    flight_id,
                    "status_id":    flight_status_id,
                    "departs_date": current.isoformat(),
                }).scalar()

                if source_sf_id:
                    copy_flight_configuration(db, source_sf_id, sf_id, flight_id)

                count += 1
            current += timedelta(days=1)

    db.flush()
    return count


def check_schedule_overlap(
    db: Session,
    flight_id: int,
    flight_season_id: int,
    schedule_groups: list[dict],
) -> list[str]:
    season = db.execute(text("""
        SELECT season_start_date, season_end_date
        FROM FlightSeason WHERE flight_season_id = :id
    """), {"id": flight_season_id}).mappings().one()

    rows = db.execute(text("""
        SELECT ds.day_id
        FROM FlightSchedule fsch
        INNER JOIN FlightSeason fsn
               ON fsn.flight_season_id      = fsch.flight_season_id
        INNER JOIN FlightScheduleDaySchedule fsds
               ON fsds.flight_schedule_id   = fsch.flight_schedule_id
        INNER JOIN DaySchedule ds
               ON ds.day_schedule_id        = fsds.day_schedule_id
        WHERE fsch.flight_id = :flight_id
          AND fsn.season_start_date <= :end_date
          AND fsn.season_end_date   >= :start_date
    """), {
        "flight_id":  flight_id,
        "start_date": season["season_start_date"],
        "end_date":   season["season_end_date"],
    }).mappings().all()

    existing_days = {row["day_id"] for row in rows}
    new_days = {d for g in schedule_groups for d in g["day_ids"]}
    overlapping = existing_days & new_days

    if not overlapping:
        return []

    day_names = {1: "Mon", 2: "Tue", 3: "Wed",
                 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    return [day_names[d] for d in sorted(overlapping)]


def check_aircraft_range(
    db: Session, airfleet_id: int, range_km: float
) -> bool:
    aircraft_range = db.execute(text("""
        SELECT aircraft_range_km FROM Airfleet
        WHERE airfleet_id = :airfleet_id
    """), {"airfleet_id": airfleet_id}).scalar()
    if aircraft_range is None:
        return True
    return float(aircraft_range) >= range_km


def generate_flight_number(db: Session, airline_id: int) -> str:
    iata = db.execute(text("""
        SELECT iata_code FROM Airline WHERE airline_id = :airline_id
    """), {"airline_id": airline_id}).scalar()
    if not iata:
        raise ValueError("Airline not found")

    rows = db.execute(text("""
        SELECT flight_number FROM Flight WHERE airline_id = :airline_id
    """), {"airline_id": airline_id}).fetchall()

    existing_numbers = set()
    for row in rows:
        num_part = row[0].replace(iata, "")
        if num_part.isdigit():
            existing_numbers.add(int(num_part))

    for _ in range(100):
        number = random.randint(100, 9999)
        if number not in existing_numbers:
            return f"{iata}{number}"

    raise ValueError("Could not generate unique flight number")


def get_all_flight_numbers(db: Session, airline_id: int) -> list[str]:
    rows = db.execute(text("""
        SELECT DISTINCT flight_number
        FROM Flight
        WHERE airline_id = :airline_id
        ORDER BY flight_number
    """), {"airline_id": airline_id}).fetchall()
    return [r[0] for r in rows]


def get_routes_with_planned_flights(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT
            r.route_id,
            f.flight_number,
            af.aircraft_model,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            COUNT(sf.schedule_flight_id) AS planned_count
        FROM Route r
        INNER JOIN Flight f     ON f.route_id      = r.route_id
        INNER JOIN Airfleet af  ON af.airfleet_id  = f.airfleet_id
        INNER JOIN Airport dep  ON dep.airport_id  = r.departs_airport_id
        INNER JOIN Airport arr  ON arr.airport_id  = r.arrives_airport_id
        INNER JOIN ScheduledFlight sf ON sf.flight_id = f.flight_id
        INNER JOIN FlightStatus fst
               ON fst.flight_status_id   = sf.flight_status_id
              AND fst.flight_status_name  = 'Auto-scheduled'
        WHERE f.airline_id = :airline_id
        GROUP BY
            r.route_id, f.flight_number,
            af.aircraft_model,
            dep.airport_code, arr.airport_code
        ORDER BY f.flight_number
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def get_planned_flights_for_route(db: Session, route_id: int) -> list:
    sql = text("""
        SELECT
            sf.schedule_flight_id,
            f.flight_id,
            f.flight_number,
            sf.departs_date,
            s.schedule_departure_time,
            s.schedule_arrival_time,
            CONVERT(VARCHAR(5), f.flight_duration, 108) AS flight_duration,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            af.aircraft_model,
            af.airfleet_id
        FROM ScheduledFlight sf
        INNER JOIN FlightStatus fst
               ON fst.flight_status_id   = sf.flight_status_id
              AND fst.flight_status_name  = 'Auto-scheduled'
        INNER JOIN Flight f     ON f.flight_id      = sf.flight_id
        INNER JOIN Airfleet af  ON af.airfleet_id   = f.airfleet_id
        INNER JOIN Route r      ON r.route_id        = f.route_id
        INNER JOIN Airport dep  ON dep.airport_id   = r.departs_airport_id
        INNER JOIN Airport arr  ON arr.airport_id   = r.arrives_airport_id
        LEFT JOIN FlightSchedule fsch ON fsch.flight_id = f.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds
               ON fsds.flight_schedule_id = fsch.flight_schedule_id
        LEFT JOIN DaySchedule ds ON ds.day_schedule_id = fsds.day_schedule_id
        LEFT JOIN Schedule s     ON s.schedule_id      = ds.schedule_id
        WHERE f.route_id = :route_id
        ORDER BY sf.departs_date
    """)
    return db.execute(sql, {"route_id": route_id}).mappings().all()


def configure_planned_flight(
    db: Session,
    schedule_flight_id: int,
    flight_id: int,
    class_prices: list[dict],
) -> None:
    for cp in class_prices:
        flight_class_id = db.execute(text("""
            INSERT INTO FlightClass (class_id, flight_id)
            OUTPUT INSERTED.flight_class_id
            VALUES (:class_id, :flight_id)
        """), {
            "class_id":  cp["class_id"],
            "flight_id": flight_id,
        }).scalar()

        db.execute(text("""
            INSERT INTO FlightPrice
                (schedule_flight_id, flight_class_id,
                 flight_published_date, ticket_price)
            VALUES
                (:schedule_flight_id, :flight_class_id,
                 CAST(GETDATE() AS DATE), :ticket_price)
        """), {
            "schedule_flight_id": schedule_flight_id,
            "flight_class_id":    flight_class_id,
            "ticket_price":       cp["price"],
        })

    scheduled_id = get_status_id_by_name(db, "Scheduled")
    db.execute(text("""
        UPDATE ScheduledFlight
        SET flight_status_id = :status_id
        WHERE schedule_flight_id = :schedule_flight_id
    """), {
        "status_id":          scheduled_id,
        "schedule_flight_id": schedule_flight_id,
    })
    db.flush()


def get_scheduled_flights_for_pricing(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT
            sf.schedule_flight_id,
            f.flight_id,
            f.flight_number,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            sf.departs_date,
            s.schedule_departure_time,
            s.schedule_arrival_time,
            CONVERT(VARCHAR(5), f.flight_duration, 108) AS flight_duration,
            af.aircraft_model,
            f.route_id,
            fst.flight_status_name
        FROM ScheduledFlight sf
        INNER JOIN FlightStatus fst
               ON fst.flight_status_id   = sf.flight_status_id
              AND fst.flight_status_name IN ('Scheduled', 'Auto-scheduled')
        INNER JOIN Flight f     ON f.flight_id     = sf.flight_id
        INNER JOIN Airfleet af  ON af.airfleet_id  = f.airfleet_id
        INNER JOIN Route r      ON r.route_id       = f.route_id
        INNER JOIN Airport dep  ON dep.airport_id  = r.departs_airport_id
        INNER JOIN Airport arr  ON arr.airport_id  = r.arrives_airport_id
        LEFT JOIN FlightSchedule fsch ON fsch.flight_id = f.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds
               ON fsds.flight_schedule_id = fsch.flight_schedule_id
        LEFT JOIN DaySchedule ds ON ds.day_schedule_id = fsds.day_schedule_id
        LEFT JOIN Schedule s     ON s.schedule_id      = ds.schedule_id
        WHERE f.airline_id = :airline_id
        ORDER BY sf.departs_date ASC, s.schedule_departure_time ASC
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def get_current_prices_for_flight(
    db: Session, schedule_flight_id: int
) -> list:
    sql = text("""
        SELECT
            fc.class_id,
            c.class_name,
            fp.ticket_price,
            fp.flight_published_date,
            fp.flight_class_id
        FROM FlightPrice fp
        INNER JOIN FlightClass fc ON fc.flight_class_id = fp.flight_class_id
        INNER JOIN Class c        ON c.class_id         = fc.class_id
        WHERE fp.schedule_flight_id = :schedule_flight_id
          AND fp.flight_published_date = (
                SELECT MAX(fp2.flight_published_date)
                FROM FlightPrice fp2
                WHERE fp2.flight_class_id    = fp.flight_class_id
                  AND fp2.schedule_flight_id = fp.schedule_flight_id
          )
        ORDER BY c.class_name
    """)
    return db.execute(
        sql, {"schedule_flight_id": schedule_flight_id}
    ).mappings().all()


def get_price_history_for_flight(
    db: Session, schedule_flight_id: int
) -> list:
    sql = text("""
        SELECT
            fp.flight_published_date,
            c.class_name,
            fp.ticket_price
        FROM FlightPrice fp
        INNER JOIN FlightClass fc ON fc.flight_class_id = fp.flight_class_id
        INNER JOIN Class c        ON c.class_id         = fc.class_id
        WHERE fp.schedule_flight_id = :schedule_flight_id
        ORDER BY fp.flight_published_date DESC, c.class_name
    """)
    return db.execute(
        sql, {"schedule_flight_id": schedule_flight_id}
    ).mappings().all()


def update_flight_prices(
    db: Session,
    schedule_flight_id: int,
    flight_id: int,
    class_prices: list[dict],
) -> None:
    for cp in class_prices:
        db.execute(text("""
            INSERT INTO FlightPrice
                (schedule_flight_id, flight_class_id,
                 flight_published_date, ticket_price)
            SELECT :schedule_flight_id, fc.flight_class_id,
                   CAST(GETDATE() AS DATE), :price
            FROM FlightClass fc
            WHERE fc.flight_id = :flight_id
              AND fc.class_id  = :class_id
        """), {
            "schedule_flight_id": schedule_flight_id,
            "flight_id":          flight_id,
            "class_id":           cp["class_id"],
            "price":              cp["price"],
        })

    scheduled_id = get_status_id_by_name(db, "Scheduled")
    db.execute(text("""
        UPDATE ScheduledFlight
        SET flight_status_id = :status_id
        WHERE schedule_flight_id = :schedule_flight_id
    """), {
        "status_id":          scheduled_id,
        "schedule_flight_id": schedule_flight_id,
    })
    db.flush()


def get_existing_route(
    db: Session,
    airline_id: int,
    airfleet_id: int,
    departs_airport_id: int,
    arrives_airport_id: int,
) -> int | None:
    return db.execute(text("""
        SELECT TOP 1 r.route_id
        FROM Route r
        INNER JOIN Flight f ON f.route_id = r.route_id
        WHERE f.airline_id          = :airline_id
          AND f.airfleet_id         = :airfleet_id
          AND r.departs_airport_id  = :departs_airport_id
          AND r.arrives_airport_id  = :arrives_airport_id
    """), {
        "airline_id":          airline_id,
        "airfleet_id":         airfleet_id,
        "departs_airport_id":  departs_airport_id,
        "arrives_airport_id":  arrives_airport_id,
    }).scalar()


def get_last_configured_scheduled_flight(
    db: Session, flight_id: int
) -> int | None:
    """Останній ScheduledFlight зі статусом Scheduled для цього flight_id."""
    return db.execute(text("""
        SELECT TOP 1 sf.schedule_flight_id
        FROM ScheduledFlight sf
        INNER JOIN FlightStatus fst
               ON fst.flight_status_id  = sf.flight_status_id
              AND fst.flight_status_name = 'Scheduled'
        INNER JOIN FlightClass fc ON fc.flight_id = sf.flight_id
        WHERE sf.flight_id = :flight_id
        ORDER BY sf.departs_date DESC
    """), {"flight_id": flight_id}).scalar()


def copy_flight_configuration(
    db: Session,
    source_sf_id: int,
    target_sf_id: int,
    flight_id: int,
) -> None:
    classes = db.execute(text("""
        SELECT class_id FROM FlightClass WHERE flight_id = :flight_id
    """), {"flight_id": flight_id}).fetchall()

    for cls in classes:
        class_id = cls[0]

        new_fc_id = db.execute(text("""
            INSERT INTO FlightClass (class_id, flight_id)
            OUTPUT INSERTED.flight_class_id
            VALUES (:class_id, :flight_id)
        """), {"class_id": class_id, "flight_id": flight_id}).scalar()

        db.execute(text("""
            INSERT INTO FlightPrice
                (schedule_flight_id, flight_class_id,
                 flight_published_date, ticket_price)
            SELECT :target_sf_id, :new_fc_id,
                   CAST(GETDATE() AS DATE), fp.ticket_price
            FROM FlightPrice fp
            INNER JOIN FlightClass fc
                   ON fc.flight_class_id = fp.flight_class_id
            WHERE fp.schedule_flight_id = :source_sf_id
              AND fc.class_id           = :class_id
              AND fp.flight_published_date = (
                    SELECT MAX(fp2.flight_published_date)
                    FROM FlightPrice fp2
                    WHERE fp2.flight_class_id    = fp.flight_class_id
                      AND fp2.schedule_flight_id = fp.schedule_flight_id
              )
        """), {
            "target_sf_id": target_sf_id,
            "new_fc_id":    new_fc_id,
            "source_sf_id": source_sf_id,
            "class_id":     class_id,
        })

        db.execute(text("""
            INSERT INTO BaggagePricingInFlight
                (flight_id, baggage_pricing_rule_id,
                 flight_class_id, baggage_price)
            SELECT :flight_id, bpif.baggage_pricing_rule_id,
                   :new_fc_id, bpif.baggage_price
            FROM BaggagePricingInFlight bpif
            INNER JOIN FlightClass fc
                   ON fc.flight_class_id = bpif.flight_class_id
            WHERE bpif.flight_id = :flight_id
              AND fc.class_id    = :class_id
        """), {
            "flight_id": flight_id,
            "new_fc_id": new_fc_id,
            "class_id":  class_id,
        })


def get_routes_with_pricing_flights(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT
            r.route_id,
            f.flight_number,
            af.aircraft_model,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            COUNT(sf.schedule_flight_id)    AS total_count,
            SUM(CASE WHEN fst.flight_status_name = 'Auto-scheduled'
                     THEN 1 ELSE 0 END)     AS auto_count,
            SUM(CASE WHEN fst.flight_status_name = 'Scheduled'
                     THEN 1 ELSE 0 END)     AS confirmed_count,
            MIN(s.schedule_departure_time)  AS departs_time,
            MIN(s.schedule_arrival_time)    AS arrives_time
        FROM Route r
        INNER JOIN Flight f     ON f.route_id     = r.route_id
        INNER JOIN Airfleet af  ON af.airfleet_id = f.airfleet_id
        INNER JOIN Airport dep  ON dep.airport_id = r.departs_airport_id
        INNER JOIN Airport arr  ON arr.airport_id = r.arrives_airport_id
        INNER JOIN ScheduledFlight sf ON sf.flight_id = f.flight_id
        INNER JOIN FlightStatus fst
               ON fst.flight_status_id   = sf.flight_status_id
              AND fst.flight_status_name  = 'Scheduled'
        LEFT JOIN FlightSchedule fsch ON fsch.flight_id = f.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds
               ON fsds.flight_schedule_id = fsch.flight_schedule_id
        LEFT JOIN DaySchedule ds ON ds.day_schedule_id = fsds.day_schedule_id
        LEFT JOIN Schedule s     ON s.schedule_id      = ds.schedule_id
        WHERE f.airline_id     = :airline_id
          AND sf.departs_date >= CAST(GETDATE() AS DATE)
        GROUP BY
            r.route_id, f.flight_number,
            af.aircraft_model,
            dep.airport_code, arr.airport_code
        ORDER BY f.flight_number
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def get_pricing_flights_for_route(db: Session, route_id: int) -> list:
    sql = text("""
        SELECT
            sf.schedule_flight_id,
            f.flight_id,
            f.flight_number,
            sf.departs_date,
            s.schedule_departure_time,
            s.schedule_arrival_time,
            CONVERT(VARCHAR(5), f.flight_duration, 108) AS flight_duration,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            fst.flight_status_name
        FROM ScheduledFlight sf
        INNER JOIN FlightStatus fst
               ON fst.flight_status_id   = sf.flight_status_id
              AND fst.flight_status_name  = 'Scheduled'
        INNER JOIN Flight f     ON f.flight_id    = sf.flight_id
        INNER JOIN Route r      ON r.route_id      = f.route_id
        INNER JOIN Airport dep  ON dep.airport_id = r.departs_airport_id
        INNER JOIN Airport arr  ON arr.airport_id = r.arrives_airport_id
        LEFT JOIN FlightSchedule fsch ON fsch.flight_id = f.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds
               ON fsds.flight_schedule_id = fsch.flight_schedule_id
        LEFT JOIN DaySchedule ds ON ds.day_schedule_id = fsds.day_schedule_id
        LEFT JOIN Schedule s     ON s.schedule_id      = ds.schedule_id
        WHERE f.route_id       = :route_id
          AND sf.departs_date >= CAST(GETDATE() AS DATE)
        ORDER BY sf.departs_date ASC, s.schedule_departure_time ASC
    """)
    return db.execute(sql, {"route_id": route_id}).mappings().all()


def get_all_flights_for_route(db: Session, route_id: int) -> list:
    sql = text("""
        SELECT
            sf.schedule_flight_id,
            f.flight_id,
            f.flight_number,
            sf.departs_date,
            s.schedule_departure_time,
            s.schedule_arrival_time,
            CONVERT(VARCHAR(5), f.flight_duration, 108) AS flight_duration,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            af.aircraft_model,
            af.airfleet_id,
            fst.flight_status_name
        FROM ScheduledFlight sf
        INNER JOIN FlightStatus fst
               ON fst.flight_status_id   = sf.flight_status_id
              AND fst.flight_status_name IN ('Auto-scheduled', 'Scheduled')
        INNER JOIN Flight f     ON f.flight_id     = sf.flight_id
        INNER JOIN Airfleet af  ON af.airfleet_id  = f.airfleet_id
        INNER JOIN Route r      ON r.route_id       = f.route_id
        INNER JOIN Airport dep  ON dep.airport_id  = r.departs_airport_id
        INNER JOIN Airport arr  ON arr.airport_id  = r.arrives_airport_id
        LEFT JOIN FlightSchedule fsch ON fsch.flight_id = f.flight_id
        LEFT JOIN FlightScheduleDaySchedule fsds
               ON fsds.flight_schedule_id = fsch.flight_schedule_id
        LEFT JOIN DaySchedule ds ON ds.day_schedule_id = fsds.day_schedule_id
        LEFT JOIN Schedule s     ON s.schedule_id      = ds.schedule_id
        WHERE f.route_id = :route_id
        ORDER BY sf.departs_date, s.schedule_departure_time
    """)
    return db.execute(sql, {"route_id": route_id}).mappings().all()


def confirm_flights(db: Session, flight_ids: list[int]) -> int:
    scheduled_id  = get_status_id_by_name(db, "Scheduled")
    auto_id       = get_status_id_by_name(db, "Auto-scheduled")

    count = 0
    for flight_id in flight_ids:
        result = db.execute(text("""
            UPDATE ScheduledFlight
            SET flight_status_id = :scheduled_id
            WHERE schedule_flight_id = :sf_id
              AND flight_status_id   = :auto_id
        """), {
            "scheduled_id": scheduled_id,
            "sf_id":        flight_id,
            "auto_id":      auto_id,
        })
        count += result.rowcount

    db.flush()
    return count


def update_flight_classes(
    db: Session,
    flight_id: int,
    class_ids: list[int],
) -> None:
    existing = {
        r[0] for r in db.execute(text("""
            SELECT class_id FROM FlightClass WHERE flight_id = :flight_id
        """), {"flight_id": flight_id}).fetchall()
    }

    for class_id in existing:
        if class_id not in class_ids:
            has_bookings = db.execute(text("""
                SELECT COUNT(*)
                FROM FlightClass fc
                INNER JOIN FlightPrice fp
                       ON fp.flight_class_id = fc.flight_class_id
                INNER JOIN BookingItem bi
                       ON bi.flight_price_id = fp.flight_price_id
                WHERE fc.flight_id = :flight_id
                  AND fc.class_id  = :class_id
            """), {
                "flight_id": flight_id,
                "class_id":  class_id,
            }).scalar()

            if not has_bookings:
                db.execute(text("""
                    DELETE FROM FlightClass
                    WHERE flight_id = :flight_id AND class_id = :class_id
                """), {"flight_id": flight_id, "class_id": class_id})

    for class_id in class_ids:
        if class_id not in existing:
            db.execute(text("""
                INSERT INTO FlightClass (class_id, flight_id)
                VALUES (:class_id, :flight_id)
            """), {"class_id": class_id, "flight_id": flight_id})

    db.flush()


def update_flight_baggage(
    db: Session,
    flight_id: int,
    baggage_options: list[dict],
) -> None:
    db.execute(text("""
        DELETE FROM BaggagePricingInFlight
        WHERE flight_id = :flight_id
          AND baggage_pricing_in_flight_id NOT IN (
                SELECT DISTINCT bpif.baggage_pricing_in_flight_id
                FROM BaggagePricingInFlight bpif
                INNER JOIN BookingBaggage bb
                       ON bb.baggage_pricing_in_flight_id =
                          bpif.baggage_pricing_in_flight_id
          )
    """), {"flight_id": flight_id})

    class_map = {
        row["class_id"]: row["flight_class_id"]
        for row in db.execute(text("""
            SELECT class_id, flight_class_id
            FROM FlightClass WHERE flight_id = :flight_id
        """), {"flight_id": flight_id}).mappings().all()
    }

    for opt in baggage_options:
        flight_class_id = class_map.get(opt["class_id"])
        if flight_class_id:
            db.execute(text("""
                INSERT INTO BaggagePricingInFlight
                    (flight_id, baggage_pricing_rule_id,
                     flight_class_id, baggage_price)
                VALUES
                    (:flight_id, :rule_id, :flight_class_id, :price)
            """), {
                "flight_id":       flight_id,
                "rule_id":         opt["baggage_pricing_rule_id"],
                "flight_class_id": flight_class_id,
                "price":           opt["price"],
            })

    db.flush()


def cancel_flight(db: Session, schedule_flight_id: int) -> None:
    cancelled_id = get_status_id_by_name(db, "Cancelled")
    if not cancelled_id:
        raise ValueError("Status 'Cancelled' does not exist in database")

    db.execute(text("""
        UPDATE ScheduledFlight
        SET flight_status_id = :sid
        WHERE schedule_flight_id = :sf_id
    """), {"sid": cancelled_id, "sf_id": schedule_flight_id})
    db.flush()


def get_flight_route_details(db: Session, flight_id: int):
    return db.execute(text("""
        SELECT f.flight_duration
        FROM Flight f
        WHERE f.flight_id = :flight_id
    """), {"flight_id": flight_id}).mappings().one_or_none()


def get_flight_reschedule_data(db: Session, flight_id: int):
    return db.execute(text("""
        SELECT
            f.airfleet_id,
            f.flight_duration,
            f.flight_number
        FROM Flight f
        WHERE f.flight_id = :flight_id
    """), {"flight_id": flight_id}).mappings().one_or_none()


def find_aircraft_overlap(
    db: Session,
    airfleet_id: int,
    exclude_schedule_flight_id: int,
    check_date: date,
) -> dict | None:
    """
    Перевіряє чи є інший ScheduledFlight з тим самим airfleet на ту саму дату.
    (Точного datetime немає — порівнюємо по даті)
    """
    return db.execute(text("""
        SELECT TOP 1 sf.schedule_flight_id, f.flight_number
        FROM ScheduledFlight sf
        INNER JOIN Flight f    ON f.flight_id    = sf.flight_id
        INNER JOIN FlightStatus fst
               ON fst.flight_status_id  = sf.flight_status_id
              AND fst.flight_status_name NOT IN ('Cancelled')
        WHERE f.airfleet_id              = :airfleet_id
          AND sf.schedule_flight_id     != :exclude_sf_id
          AND sf.departs_date            = :check_date
    """), {
        "airfleet_id":   airfleet_id,
        "exclude_sf_id": exclude_schedule_flight_id,
        "check_date":    check_date,
    }).mappings().first()


def update_scheduled_flight_date(
    db: Session,
    schedule_flight_id: int,
    departs_date: date,
) -> None:
    db.execute(text("""
        UPDATE ScheduledFlight
        SET departs_date = :departs_date
        WHERE schedule_flight_id = :sf_id
    """), {"departs_date": departs_date, "sf_id": schedule_flight_id})
    db.flush()