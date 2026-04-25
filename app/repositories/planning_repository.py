from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, timedelta
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
    conditions = ["al.airline_id = :airline_id"]
    params: dict = {"airline_id": airline_id}

    if mode == "day" and date:
        conditions.append("CAST(f.departs_datetime AS DATE) = :date")
        params["date"] = date
    elif mode == "month" and month and year:
        conditions.append("MONTH(f.departs_datetime) = :month")
        conditions.append("YEAR(f.departs_datetime) = :year")
        params["month"] = month
        params["year"] = year

    if status:
        conditions.append("fs.flight_status_name = :status")
        params["status"] = status

    if flight_number:
        conditions.append("r.flight_number LIKE :flight_number")
        params["flight_number"] = f"%{flight_number}%"

    where = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            f.flight_id,
            r.flight_number,
            dep_air.airport_code   AS departs_code,
            arr_air.airport_code   AS arrives_code,
            f.departs_datetime,
            f.arrives_datetime,
            CONVERT(VARCHAR(5), r.flight_duration, 108) AS flight_duration,
            fs.flight_status_name,
            af.aircraft_model,
            af.seat_capacity,
            STRING_AGG(c.class_name, ', ') WITHIN GROUP (ORDER BY c.class_name) AS classes,
            COUNT(DISTINCT bi.booking_item_id) AS booked_seats
        FROM Flight f
        INNER JOIN FlightSchedule fsched ON f.flight_schedule_id = fsched.flight_schedule_id
        INNER JOIN Route r              ON fsched.route_id = r.route_id
        INNER JOIN Airline al           ON r.airline_id = al.airline_id
        INNER JOIN Airfleet af          ON r.airfleet_id = af.airfleet_id
        INNER JOIN Airport dep_air      ON r.departs_airport_id = dep_air.airport_id
        INNER JOIN Airport arr_air      ON r.arrives_airport_id = arr_air.airport_id
        INNER JOIN FlightStatus fs      ON f.flight_status_id = fs.flight_status_id
        LEFT JOIN FlightClass fc       ON f.flight_id = fc.flight_id
        INNER JOIN Class c              ON fc.class_id = c.class_id
        INNER JOIN FlightPrice fp ON fc.flight_class_id = fp.flight_class_id
            AND fp.flight_published_date = (
                SELECT MAX(fp2.flight_published_date)
                FROM FlightPrice fp2
                WHERE fp2.flight_class_id = fc.flight_class_id
            )
        LEFT JOIN BookingItem bi ON bi.flight_price_id = fp.flight_price_id
        LEFT JOIN Booking b      ON bi.booking_id = b.booking_id
        LEFT JOIN BookingStatus bs ON b.booking_status_id = bs.booking_status_id
            AND bs.booking_status_name IN ('Confirmed', 'Completed')
        WHERE {where}
        GROUP BY
            f.flight_id, r.flight_number,
            dep_air.airport_code, arr_air.airport_code,
            f.departs_datetime, f.arrives_datetime,
            r.flight_duration, fs.flight_status_name,
            af.aircraft_model, af.seat_capacity
        ORDER BY f.departs_datetime ASC
    """)

    result = db.execute(sql, params)
    return result.mappings().all()


def get_overview_stats(db: Session, airline_id: int):
    sql = text("""
        WITH FlightBase AS (
            SELECT
                f.flight_id,
                af.seat_capacity,
                fs.flight_status_name,
                r.route_id
            FROM Flight f
            INNER JOIN FlightSchedule fsched ON f.flight_schedule_id = fsched.flight_schedule_id
            INNER JOIN Route r              ON fsched.route_id = r.route_id
            INNER JOIN Airline al           ON r.airline_id = al.airline_id
            INNER JOIN Airfleet af          ON r.airfleet_id = af.airfleet_id
            INNER JOIN FlightStatus fs      ON f.flight_status_id = fs.flight_status_id
            WHERE al.airline_id = :airline_id
        ),
        ActiveFlights AS (
            SELECT flight_id, seat_capacity, route_id
            FROM FlightBase
            WHERE flight_status_name IN ('Scheduled', 'Boarding', 'Departed')
        ),
        BookedSeats AS (
            SELECT
                fc.flight_id,
                COUNT(DISTINCT bi.booking_item_id) AS booked_count
            FROM FlightClass fc
            INNER JOIN FlightPrice fp ON fc.flight_class_id = fp.flight_class_id
                AND fp.flight_published_date = (
                    SELECT MAX(fp2.flight_published_date)
                    FROM FlightPrice fp2
                    WHERE fp2.flight_class_id = fc.flight_class_id
                )
            INNER JOIN BookingItem bi ON bi.flight_price_id = fp.flight_price_id
            INNER JOIN Booking b      ON bi.booking_id = b.booking_id
            INNER JOIN BookingStatus bs ON b.booking_status_id = bs.booking_status_id
                AND bs.booking_status_name IN ('Confirmed', 'Completed')
            WHERE fc.flight_id IN (SELECT flight_id FROM ActiveFlights)
            GROUP BY fc.flight_id
        ),
        MonthlyRevenue AS (
            SELECT COALESCE(SUM(p.payment_amount), 0) AS revenue
            FROM Payment p
            INNER JOIN PaymentStatus ps ON p.payment_status_id = ps.payment_status_id
                AND ps.payment_status_name = 'Completed'
            INNER JOIN Booking b   ON p.booking_id = b.booking_id
            INNER JOIN BookingItem bi ON bi.booking_id = b.booking_id
            INNER JOIN FlightPrice fp ON bi.flight_price_id = fp.flight_price_id
            INNER JOIN FlightClass fc ON fp.flight_class_id = fc.flight_class_id
            INNER JOIN Flight f        ON fc.flight_id = f.flight_id
            INNER JOIN FlightSchedule fsched ON f.flight_schedule_id = fsched.flight_schedule_id
            INNER JOIN Route r         ON fsched.route_id = r.route_id
            INNER JOIN Airline al      ON r.airline_id = al.airline_id
            WHERE al.airline_id = :airline_id
              AND MONTH(p.payment_date_time) = MONTH(GETDATE())
              AND YEAR(p.payment_date_time)  = YEAR(GETDATE())
        )
        SELECT
            (SELECT COUNT(*) FROM ActiveFlights)                         AS active_flights_count,
            (SELECT COUNT(DISTINCT route_id) FROM ActiveFlights)         AS routes_count,
            (
                SELECT COALESCE(
                    AVG(
                        CAST(bs.booked_count AS FLOAT) /
                        NULLIF(af.seat_capacity, 0) * 100
                    ), 0)
                FROM ActiveFlights af
                LEFT JOIN BookedSeats bs ON af.flight_id = bs.flight_id
            )                                                            AS average_load_percent,
            (SELECT revenue FROM MonthlyRevenue)                         AS monthly_revenue_eur
    """)

    result = db.execute(sql, {"airline_id": airline_id})
    return result.mappings().one()


def get_available_dates(db: Session, airline_id: int) -> list[str]:
    sql = text("""
        SELECT DISTINCT CAST(f.departs_datetime AS DATE) AS flight_date
        FROM Flight f
        INNER JOIN FlightSchedule fsched ON f.flight_schedule_id = fsched.flight_schedule_id
        INNER JOIN Route r ON fsched.route_id = r.route_id
        INNER JOIN Airline al ON r.airline_id = al.airline_id
        WHERE al.airline_id = :airline_id
        ORDER BY flight_date ASC
    """)
    result = db.execute(sql, {"airline_id": airline_id})
    return [str(row["flight_date"]) for row in result.mappings().all()]


def get_booked_dates_for_schedule(db: Session, flight_schedule_id: int) -> list[str]:
    sql = text("""
        SELECT DISTINCT CAST(f.departs_datetime AS DATE) AS flight_date
        FROM Flight f
        WHERE f.flight_schedule_id = :flight_schedule_id
        ORDER BY flight_date ASC
    """)
    result = db.execute(sql, {"flight_schedule_id": flight_schedule_id})
    return [str(row["flight_date"]) for row in result.mappings().all()]


def get_available_months(db: Session, airline_id: int) -> list[str]:
    sql = text("""
        SELECT DISTINCT
            YEAR(f.departs_datetime)  AS yr,
            MONTH(f.departs_datetime) AS mo
        FROM Flight f
        INNER JOIN FlightSchedule fsched ON f.flight_schedule_id = fsched.flight_schedule_id
        INNER JOIN Route r ON fsched.route_id = r.route_id
        INNER JOIN Airline al ON r.airline_id = al.airline_id
        WHERE al.airline_id = :airline_id
        ORDER BY yr, mo
    """)
    result = db.execute(sql, {"airline_id": airline_id})
    return [
        f"{row['yr']}-{str(row['mo']).zfill(2)}"
        for row in result.mappings().all()
    ]


def get_routes_for_airline(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT
            r.route_id,
            r.flight_number,
            r.airfleet_id,
            af.aircraft_model,
            af.seat_capacity,
            dep.airport_code AS departs_code,
            dep.airport_name AS departs_airport,
            arr.airport_code AS arrives_code,
            arr.airport_name AS arrives_airport,
            CONVERT(VARCHAR(5), r.flight_duration, 108) AS flight_duration
        FROM Route r
        INNER JOIN Airline al ON r.airline_id = al.airline_id
        INNER JOIN Airfleet af ON r.airfleet_id = af.airfleet_id
        INNER JOIN Airport dep ON r.departs_airport_id = dep.airport_id
        INNER JOIN Airport arr ON r.arrives_airport_id = arr.airport_id
        WHERE al.airline_id = :airline_id
        ORDER BY r.flight_number
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def get_route_schedules(db: Session, route_id: int) -> list:
    sql = text("""
        SELECT
            fs.flight_schedule_id,
            fs.flight_start_date,
            fs.flight_end_date,
            ds.day_id,
            d.day_name,
            s.schedule_departure_time,
            s.schedule_arrival_time
        FROM FlightSchedule fs
        INNER JOIN FlightScheduleDaySchedule fds
            ON fds.flight_schedule_id = fs.flight_schedule_id
        INNER JOIN DaySchedule ds ON ds.day_schedule_id = fds.day_schedule_id
        INNER JOIN Schedule s ON s.schedule_id = ds.schedule_id
        INNER JOIN DayForSchedule d ON d.day_id = ds.day_id
        WHERE fs.route_id = :route_id
        ORDER BY fs.flight_schedule_id, ds.day_id
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
        INNER JOIN Class c ON sl.class_id = c.class_id
        INNER JOIN SeatType st ON sl.seat_type_id = st.seat_type_id
        WHERE sl.airfleet_id = :airfleet_id
        ORDER BY sl.seat_layout_rows, sl.seat_layout_columns
    """)
    return db.execute(sql, {"airfleet_id": airfleet_id}).mappings().all()


def get_status_id_by_name(db: Session, status_name: str) -> int:
    sql = text("SELECT flight_status_id FROM FlightStatus WHERE flight_status_name = :status_name")
    return db.execute(sql, {"status_name": status_name}).scalar()


def create_flight(
    db: Session,
    flight_schedule_id: int,
    flight_status_id: int,
    departs_datetime: str,
    arrives_datetime: str,
    class_prices: list[dict],
) -> int:
    sql_flight = text("""
        INSERT INTO Flight (flight_schedule_id, flight_status_id, departs_datetime, arrives_datetime)
        OUTPUT INSERTED.flight_id
        VALUES (:flight_schedule_id, :flight_status_id, :departs_datetime, :arrives_datetime)
    """)
    result = db.execute(sql_flight, {
        "flight_schedule_id": flight_schedule_id,
        "flight_status_id": flight_status_id,
        "departs_datetime": departs_datetime,
        "arrives_datetime": arrives_datetime,
    })
    flight_id = result.scalar()

    for cp in class_prices:
        sql_fc = text("""
            INSERT INTO FlightClass (class_id, flight_id)
            OUTPUT INSERTED.flight_class_id
            VALUES (:class_id, :flight_id)
        """)
        fc_result = db.execute(sql_fc, {
            "class_id": cp["class_id"],
            "flight_id": flight_id,
        })
        flight_class_id = fc_result.scalar()

        sql_fp = text("""
            INSERT INTO FlightPrice (flight_class_id, flight_published_date, ticket_price)
            VALUES (:flight_class_id, CAST(GETDATE() AS DATE), :ticket_price)
        """)
        db.execute(sql_fp, {
            "flight_class_id": flight_class_id,
            "ticket_price": cp["price"],
        })

    db.commit()
    return flight_id


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
        INNER JOIN BaggageType bt ON bpr.baggage_type_id = bt.baggage_type_id
        ORDER BY bt.baggage_type_id, bpr.baggage_max_weight
    """)
    return db.execute(sql).mappings().all()


def add_baggage_to_flight(db: Session, flight_id: int, baggage_options: list[dict]):
    find_fc_sql = text("""
        SELECT class_id, flight_class_id 
        FROM FlightClass 
        WHERE flight_id = :flight_id
    """)
    flight_classes = db.execute(find_fc_sql, {"flight_id": flight_id}).mappings().all()
    
    class_map = {row["class_id"]: row["flight_class_id"] for row in flight_classes}

    insert_sql = text("""
        INSERT INTO BaggagePricingInFlight 
            (flight_id, baggage_pricing_rule_id, flight_class_id, baggage_price)
        VALUES 
            (:flight_id, :rule_id, :flight_class_id, :price)
    """)

    for opt in baggage_options:
        flight_class_id = class_map.get(opt["class_id"])
        
        if flight_class_id:
            db.execute(insert_sql, {
                "flight_id": flight_id,
                "rule_id": opt["baggage_pricing_rule_id"],
                "flight_class_id": flight_class_id,
                "price": opt["price"]
            })
    
    db.commit()


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
        INNER JOIN AirlineAirfleet aa ON af.airfleet_id = aa.airfleet_id
        INNER JOIN AirfleetManufacturer m ON af.airfleet_manufacturer_id = m.airfleet_manufacturer_id
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
            a.latitude,
            a.longitude,
            c.city_name,
            co.country_name
        FROM Airport a
        INNER JOIN City c ON a.city_id = c.city_id
        INNER JOIN Country co ON c.country_id = co.country_id
        INNER JOIN Route r ON (
            r.departs_airport_id = a.airport_id OR
            r.arrives_airport_id = a.airport_id
        )
        INNER JOIN Airline al ON r.airline_id = al.airline_id
        WHERE al.airline_id = :airline_id
        ORDER BY a.airport_code
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def check_flight_number_exists(db: Session, flight_number: str) -> bool:
    sql = text("""
        SELECT COUNT(*) FROM Route WHERE flight_number = :flight_number
    """)
    count = db.execute(sql, {"flight_number": flight_number}).scalar()
    return count > 0


def calculate_route_range_and_duration(
    db: Session,
    departs_airport_id: int,
    arrives_airport_id: int,
    airfleet_id: int,
) -> dict:
    sql = text("""
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
    """)
    row = db.execute(sql, {
        "dep_id": departs_airport_id,
        "arr_id": arrives_airport_id,
        "airfleet_id": airfleet_id,
    }).mappings().one()

    import math
    lat1 = math.radians(float(row["dep_lat"]))
    lon1 = math.radians(float(row["dep_lon"]))
    lat2 = math.radians(float(row["arr_lat"]))
    lon2 = math.radians(float(row["arr_lon"]))

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    range_km = round(6371 * c, 2)

    speed = float(row["aircraft_speed"]) if row["aircraft_speed"] else 850.0
    duration_hours = range_km / speed
    total_minutes = int(round(duration_hours * 60))
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
    sql = text("""
        INSERT INTO Route (
            airline_id, airfleet_id,
            departs_airport_id, arrives_airport_id,
            flight_number, flight_range, flight_duration
        )
        OUTPUT INSERTED.route_id
        VALUES (
            :airline_id, :airfleet_id,
            :departs_airport_id, :arrives_airport_id,
            :flight_number, :flight_range, :flight_duration
        )
    """)
    result = db.execute(sql, {
        "airline_id": airline_id,
        "airfleet_id": airfleet_id,
        "departs_airport_id": departs_airport_id,
        "arrives_airport_id": arrives_airport_id,
        "flight_number": flight_number,
        "flight_range": flight_range,
        "flight_duration": flight_duration,
    })
    return result.scalar()


def create_schedule_for_route(
    db: Session,
    route_id: int,
    flight_start_date: str,
    flight_end_date: str,
    schedule_groups: list[dict],
) -> int:
    from datetime import datetime, timedelta

    sql_duration = text("""
        SELECT CONVERT(VARCHAR(5), r.flight_duration, 108) AS flight_duration
        FROM Route r WHERE r.route_id = :route_id
    """)
    duration_str = db.execute(sql_duration, {"route_id": route_id}).scalar()
    h, m = map(int, duration_str.split(":"))
    duration_delta = timedelta(hours=h, minutes=m)

    sql_fs = text("""
        INSERT INTO FlightSchedule (route_id, flight_start_date, flight_end_date)
        OUTPUT INSERTED.flight_schedule_id
        VALUES (:route_id, :flight_start_date, :flight_end_date)
    """)
    result = db.execute(sql_fs, {
        "route_id": route_id,
        "flight_start_date": flight_start_date,
        "flight_end_date": flight_end_date,
    })
    flight_schedule_id = result.scalar()

    for group in schedule_groups:
        dep_time = group["departure_time"]
        dep_dt = datetime.strptime(dep_time, "%H:%M")
        arr_dt = dep_dt + duration_delta
        arr_time = arr_dt.strftime("%H:%M")

        sql_s = text("""
            INSERT INTO Schedule (schedule_departure_time, schedule_arrival_time)
            OUTPUT INSERTED.schedule_id
            VALUES (:dep_time, :arr_time)
        """)
        schedule_id = db.execute(sql_s, {
            "dep_time": dep_time,
            "arr_time": arr_time,
        }).scalar()

        for day_id in group["day_ids"]:
            sql_ds = text("""
                INSERT INTO DaySchedule (schedule_id, day_id)
                OUTPUT INSERTED.day_schedule_id
                VALUES (:schedule_id, :day_id)
            """)
            day_schedule_id = db.execute(sql_ds, {
                "schedule_id": schedule_id,
                "day_id": day_id,
            }).scalar()

            sql_link = text("""
                INSERT INTO FlightScheduleDaySchedule
                    (flight_schedule_id, day_schedule_id)
                VALUES (:flight_schedule_id, :day_schedule_id)
            """)
            db.execute(sql_link, {
                "flight_schedule_id": flight_schedule_id,
                "day_schedule_id": day_schedule_id,
            })

    return flight_schedule_id


def generate_flights_for_schedule(
    db: Session,
    flight_schedule_id: int,
    route_id: int,
    flight_start_date: str,
    flight_end_date: str,
    schedule_groups: list[dict],
    flight_status_id: int,
) -> int:
    sql_duration = text("""
        SELECT CONVERT(VARCHAR(5), r.flight_duration, 108) AS flight_duration
        FROM Route r WHERE r.route_id = :route_id
    """)
    duration_str = db.execute(sql_duration, {"route_id": route_id}).scalar()
    h, m = map(int, duration_str.split(":"))
    duration_delta = timedelta(hours=h, minutes=m)

    day_map = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6}
    start = date.fromisoformat(flight_start_date)
    end = date.fromisoformat(flight_end_date)

    source_flight_id = get_last_configured_flight_for_route(db, route_id)

    sql_flight = text("""
        INSERT INTO Flight (
            flight_schedule_id, flight_status_id,
            departs_datetime, arrives_datetime
        )
        OUTPUT INSERTED.flight_id
        VALUES (
            :flight_schedule_id, :flight_status_id,
            :departs_datetime, :arrives_datetime
        )
    """)

    count = 0
    for group in schedule_groups:
        weekdays = {day_map[d] for d in group["day_ids"]}
        dep_time = group["departure_time"]
        current = start
        while current <= end:
            if current.weekday() in weekdays:
                from datetime import datetime
                dep_dt = datetime.fromisoformat(f"{current}T{dep_time}:00")
                arr_dt = dep_dt + duration_delta

                result = db.execute(sql_flight, {
                    "flight_schedule_id": flight_schedule_id,
                    "flight_status_id": flight_status_id,
                    "departs_datetime": dep_dt.isoformat(),
                    "arrives_datetime": arr_dt.isoformat(),
                })
                new_flight_id = result.scalar()

                if source_flight_id:
                    copy_flight_configuration(db, source_flight_id, new_flight_id)

                count += 1
            current += timedelta(days=1)

    return count


def check_schedule_overlap(
    db: Session,
    route_id: int,
    flight_start_date: str,
    flight_end_date: str,
    schedule_groups: list[dict],
) -> list[str]:
    sql = text("""
        SELECT
            fs.flight_schedule_id,
            fs.flight_start_date,
            fs.flight_end_date,
            ds.day_id
        FROM FlightSchedule fs
        INNER JOIN FlightScheduleDaySchedule fds
            ON fds.flight_schedule_id = fs.flight_schedule_id
        INNER JOIN DaySchedule ds ON ds.day_schedule_id = fds.day_schedule_id
        WHERE fs.route_id = :route_id
          AND fs.flight_start_date <= :end_date
          AND fs.flight_end_date >= :start_date
    """)
    rows = db.execute(sql, {
        "route_id": route_id,
        "start_date": flight_start_date,
        "end_date": flight_end_date,
    }).mappings().all()

    existing_days = {row["day_id"] for row in rows}

    new_days = set()
    for group in schedule_groups:
        for day_id in group["day_ids"]:
            new_days.add(day_id)

    overlapping_days = existing_days & new_days
    if not overlapping_days:
        return []

    day_names = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
    return [day_names[d] for d in sorted(overlapping_days)]


def check_aircraft_range(
    db: Session,
    airfleet_id: int,
    range_km: float,
) -> bool:
    sql = text("""
        SELECT aircraft_range_km FROM Airfleet
        WHERE airfleet_id = :airfleet_id
    """)
    aircraft_range = db.execute(sql, {"airfleet_id": airfleet_id}).scalar()
    if aircraft_range is None:
        return True
    return float(aircraft_range) >= range_km


def generate_flight_number(db: Session, airline_id: int) -> str:
    sql_iata = text("""
        SELECT iata_code FROM Airline WHERE airline_id = :airline_id
    """)
    iata = db.execute(sql_iata, {"airline_id": airline_id}).scalar()
    if not iata:
        raise ValueError("Airline not found")

    sql_existing = text("""
        SELECT r.flight_number
        FROM Route r
        WHERE r.airline_id = :airline_id
    """)
    rows = db.execute(sql_existing, {"airline_id": airline_id}).fetchall()
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
    sql = text("""
        SELECT DISTINCT flight_number 
        FROM Route 
        WHERE airline_id = :airline_id
        ORDER BY flight_number
    """)
    rows = db.execute(sql, {"airline_id": airline_id}).fetchall()
    return [r[0] for r in rows]


def get_routes_with_planned_flights(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT
            r.route_id,
            r.flight_number,
            af.aircraft_model,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            COUNT(f.flight_id) AS planned_count
        FROM Route r
        INNER JOIN Airline al ON r.airline_id = al.airline_id
        INNER JOIN Airfleet af ON r.airfleet_id = af.airfleet_id
        INNER JOIN Airport dep ON r.departs_airport_id = dep.airport_id
        INNER JOIN Airport arr ON r.arrives_airport_id = arr.airport_id
        INNER JOIN FlightSchedule fs ON fs.route_id = r.route_id
        INNER JOIN Flight f ON f.flight_schedule_id = fs.flight_schedule_id
        INNER JOIN FlightStatus fst ON f.flight_status_id = fst.flight_status_id
        WHERE al.airline_id = :airline_id
          AND fst.flight_status_name = 'Auto-scheduled'
        GROUP BY
            r.route_id, r.flight_number,
            af.aircraft_model,
            dep.airport_code, arr.airport_code
        ORDER BY r.flight_number
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def get_planned_flights_for_route(db: Session, route_id: int) -> list:
    sql = text("""
        SELECT
            f.flight_id,
            r.flight_number,
            f.departs_datetime,
            f.arrives_datetime,
            CONVERT(VARCHAR(5), r.flight_duration, 108) AS flight_duration,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            af.aircraft_model,
            af.airfleet_id
        FROM Flight f
        INNER JOIN FlightSchedule fs ON f.flight_schedule_id = fs.flight_schedule_id
        INNER JOIN Route r ON fs.route_id = r.route_id
        INNER JOIN Airfleet af ON r.airfleet_id = af.airfleet_id
        INNER JOIN Airport dep ON r.departs_airport_id = dep.airport_id
        INNER JOIN Airport arr ON r.arrives_airport_id = arr.airport_id
        INNER JOIN FlightStatus fst ON f.flight_status_id = fst.flight_status_id
        WHERE r.route_id = :route_id
          AND fst.flight_status_name = 'Auto-scheduled'
        ORDER BY f.departs_datetime
    """)
    return db.execute(sql, {"route_id": route_id}).mappings().all()


def configure_planned_flight(
    db: Session,
    flight_id: int,
    class_prices: list[dict],
) -> None:
    for cp in class_prices:
        sql_fc = text("""
            INSERT INTO FlightClass (class_id, flight_id)
            OUTPUT INSERTED.flight_class_id
            VALUES (:class_id, :flight_id)
        """)
        fc_result = db.execute(sql_fc, {
            "class_id": cp["class_id"],
            "flight_id": flight_id,
        })
        flight_class_id = fc_result.scalar()

        sql_fp = text("""
            INSERT INTO FlightPrice (flight_class_id, flight_published_date, ticket_price)
            VALUES (:flight_class_id, CAST(GETDATE() AS DATE), :ticket_price)
        """)
        db.execute(sql_fp, {
            "flight_class_id": flight_class_id,
            "ticket_price": cp["price"],
        })

    scheduled_id = get_status_id_by_name(db, "Scheduled")
    db.execute(text("""
        UPDATE Flight SET flight_status_id = :status_id
        WHERE flight_id = :flight_id
    """), {"status_id": scheduled_id, "flight_id": flight_id})

    db.commit()


def get_scheduled_flights_for_pricing(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT
            f.flight_id,
            r.flight_number,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            f.departs_datetime,
            f.arrives_datetime,
            CONVERT(VARCHAR(5), r.flight_duration, 108) AS flight_duration,
            af.aircraft_model,
            r.route_id,
            fst.flight_status_name
        FROM Flight f
        INNER JOIN FlightSchedule fs ON f.flight_schedule_id = fs.flight_schedule_id
        INNER JOIN Route r ON fs.route_id = r.route_id
        INNER JOIN Airline al ON r.airline_id = al.airline_id
        INNER JOIN Airfleet af ON r.airfleet_id = af.airfleet_id
        INNER JOIN Airport dep ON r.departs_airport_id = dep.airport_id
        INNER JOIN Airport arr ON r.arrives_airport_id = arr.airport_id
        INNER JOIN FlightStatus fst ON f.flight_status_id = fst.flight_status_id
        WHERE al.airline_id = :airline_id
          AND fst.flight_status_name IN ('Scheduled', 'Auto-scheduled')
        ORDER BY f.departs_datetime ASC
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def get_current_prices_for_flight(db: Session, flight_id: int) -> list:
    sql = text("""
        SELECT
            fc.class_id,
            c.class_name,
            fp.ticket_price,
            fp.flight_published_date,
            fp.flight_class_id
        FROM FlightClass fc
        INNER JOIN Class c ON fc.class_id = c.class_id
        INNER JOIN FlightPrice fp ON fc.flight_class_id = fp.flight_class_id
            AND fp.flight_published_date = (
                SELECT MAX(fp2.flight_published_date)
                FROM FlightPrice fp2
                WHERE fp2.flight_class_id = fc.flight_class_id
            )
        WHERE fc.flight_id = :flight_id
        ORDER BY c.class_name
    """)
    return db.execute(sql, {"flight_id": flight_id}).mappings().all()


def get_price_history_for_flight(db: Session, flight_id: int) -> list:
    sql = text("""
        SELECT
            fp.flight_published_date,
            c.class_name,
            fp.ticket_price
        FROM FlightClass fc
        INNER JOIN Class c ON fc.class_id = c.class_id
        INNER JOIN FlightPrice fp ON fc.flight_class_id = fp.flight_class_id
        WHERE fc.flight_id = :flight_id
        ORDER BY fp.flight_published_date DESC, c.class_name
    """)
    return db.execute(sql, {"flight_id": flight_id}).mappings().all()


def update_flight_prices(
    db: Session,
    flight_id: int,
    class_prices: list[dict],
) -> None:
    for cp in class_prices:
        sql = text("""
            INSERT INTO FlightPrice (flight_class_id, flight_published_date, ticket_price)
            SELECT fc.flight_class_id, CAST(GETDATE() AS DATE), :price
            FROM FlightClass fc
            WHERE fc.flight_id = :flight_id
              AND fc.class_id = :class_id
        """)
        db.execute(sql, {
            "flight_id": flight_id,
            "class_id": cp["class_id"],
            "price": cp["price"],
        })

    scheduled_id = get_status_id_by_name(db, "Scheduled")
    db.execute(text("""
        UPDATE Flight SET flight_status_id = :status_id
        WHERE flight_id = :flight_id
    """), {"status_id": scheduled_id, "flight_id": flight_id})

    db.commit()


def get_existing_route(
    db: Session,
    airline_id: int,
    airfleet_id: int,
    departs_airport_id: int,
    arrives_airport_id: int,
) -> int | None:
    sql = text("""
        SELECT TOP 1 route_id FROM Route
        WHERE airline_id = :airline_id
          AND airfleet_id = :airfleet_id
          AND departs_airport_id = :departs_airport_id
          AND arrives_airport_id = :arrives_airport_id
    """)
    return db.execute(sql, {
        "airline_id": airline_id,
        "airfleet_id": airfleet_id,
        "departs_airport_id": departs_airport_id,
        "arrives_airport_id": arrives_airport_id,
    }).scalar()


def get_last_configured_flight_for_route(db: Session, route_id: int) -> int | None:
    sql = text("""
        SELECT TOP 1 f.flight_id
        FROM Flight f
        INNER JOIN FlightSchedule fs ON f.flight_schedule_id = fs.flight_schedule_id
        INNER JOIN Route r ON fs.route_id = r.route_id
        INNER JOIN FlightStatus fst ON f.flight_status_id = fst.flight_status_id
        INNER JOIN FlightClass fc ON fc.flight_id = f.flight_id
        WHERE fst.flight_status_name = 'Scheduled'
          AND r.departs_airport_id = (
              SELECT departs_airport_id FROM Route WHERE route_id = :route_id)
          AND r.arrives_airport_id = (
              SELECT arrives_airport_id FROM Route WHERE route_id = :route_id)
          AND r.airline_id = (
              SELECT airline_id FROM Route WHERE route_id = :route_id)
        ORDER BY f.departs_datetime DESC
    """)
    return db.execute(sql, {"route_id": route_id}).scalar()


def copy_flight_configuration(
    db: Session,
    source_flight_id: int,
    target_flight_id: int,
) -> None:
    sql_classes = text("""
        SELECT class_id FROM FlightClass
        WHERE flight_id = :flight_id
    """)
    classes = db.execute(sql_classes,
        {"flight_id": source_flight_id}).fetchall()

    for cls in classes:
        class_id = cls[0]

        sql_fc = text("""
            INSERT INTO FlightClass (class_id, flight_id)
            OUTPUT INSERTED.flight_class_id
            VALUES (:class_id, :flight_id)
        """)
        new_fc_id = db.execute(sql_fc, {
            "class_id": class_id,
            "flight_id": target_flight_id,
        }).scalar()

        sql_price = text("""
            INSERT INTO FlightPrice (flight_class_id, flight_published_date, ticket_price)
            SELECT :new_fc_id, CAST(GETDATE() AS DATE), fp.ticket_price
            FROM FlightClass fc
            INNER JOIN FlightPrice fp ON fc.flight_class_id = fp.flight_class_id
                AND fp.flight_published_date = (
                    SELECT MAX(fp2.flight_published_date)
                    FROM FlightPrice fp2
                    WHERE fp2.flight_class_id = fc.flight_class_id
                )
            WHERE fc.flight_id = :source_flight_id
              AND fc.class_id = :class_id
        """)
        db.execute(sql_price, {
            "new_fc_id": new_fc_id,
            "source_flight_id": source_flight_id,
            "class_id": class_id,
        })

        sql_baggage = text("""
            INSERT INTO BaggagePricingInFlight
                (flight_id, baggage_pricing_rule_id, flight_class_id, baggage_price)
            SELECT :target_flight_id, bpif.baggage_pricing_rule_id,
                   :new_fc_id, bpif.baggage_price
            FROM BaggagePricingInFlight bpif
            INNER JOIN FlightClass fc ON bpif.flight_class_id = fc.flight_class_id
            WHERE bpif.flight_id = :source_flight_id
              AND fc.class_id = :class_id
        """)
        db.execute(sql_baggage, {
            "target_flight_id": target_flight_id,
            "new_fc_id": new_fc_id,
            "source_flight_id": source_flight_id,
            "class_id": class_id,
        })


def get_routes_with_pricing_flights(db: Session, airline_id: int) -> list:
    sql = text("""
        SELECT
            r.route_id,
            r.flight_number,
            af.aircraft_model,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            COUNT(f.flight_id) AS total_count,
            SUM(CASE WHEN fst.flight_status_name = 'Auto-scheduled' THEN 1 ELSE 0 END) AS auto_count,
            SUM(CASE WHEN fst.flight_status_name = 'Scheduled' THEN 1 ELSE 0 END) AS confirmed_count,
            MIN(CONVERT(VARCHAR(5), f.departs_datetime, 108)) AS departs_time,
            MIN(CONVERT(VARCHAR(5), f.arrives_datetime, 108)) AS arrives_time
        FROM Route r
        INNER JOIN Airline al ON r.airline_id = al.airline_id
        INNER JOIN Airfleet af ON r.airfleet_id = af.airfleet_id
        INNER JOIN Airport dep ON r.departs_airport_id = dep.airport_id
        INNER JOIN Airport arr ON r.arrives_airport_id = arr.airport_id
        INNER JOIN FlightSchedule fs ON fs.route_id = r.route_id
        INNER JOIN Flight f ON f.flight_schedule_id = fs.flight_schedule_id
        INNER JOIN FlightStatus fst ON f.flight_status_id = fst.flight_status_id
        WHERE al.airline_id = :airline_id
          AND fst.flight_status_name IN ('Scheduled')
               AND CAST(f.departs_datetime AS DATE) >= CAST(GETDATE() AS DATE)
        GROUP BY
            r.route_id, r.flight_number,
            af.aircraft_model,
            dep.airport_code, arr.airport_code
        ORDER BY r.flight_number
    """)
    return db.execute(sql, {"airline_id": airline_id}).mappings().all()


def get_pricing_flights_for_route(db: Session, route_id: int) -> list:
    sql = text("""
        SELECT
            f.flight_id,
            r.flight_number,
            f.departs_datetime,
            f.arrives_datetime,
            CONVERT(VARCHAR(5), r.flight_duration, 108) AS flight_duration,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            fst.flight_status_name
        FROM Flight f
        INNER JOIN FlightSchedule fs ON f.flight_schedule_id = fs.flight_schedule_id
        INNER JOIN Route r ON fs.route_id = r.route_id
        INNER JOIN Airport dep ON r.departs_airport_id = dep.airport_id
        INNER JOIN Airport arr ON r.arrives_airport_id = arr.airport_id
        INNER JOIN FlightStatus fst ON f.flight_status_id = fst.flight_status_id
        WHERE r.route_id = :route_id
          AND fst.flight_status_name IN ('Scheduled')
               AND CAST(f.departs_datetime AS DATE) >= CAST(GETDATE() AS DATE)AND CAST(f.departs_datetime AS DATE) >= CAST(GETDATE() AS DATE)
        ORDER BY f.departs_datetime ASC
    """)
    return db.execute(sql, {"route_id": route_id}).mappings().all()


def get_all_flights_for_route(db: Session, route_id: int) -> list:
    sql = text("""
        SELECT
            f.flight_id,
            r.flight_number,
            f.departs_datetime,
            f.arrives_datetime,
            CONVERT(VARCHAR(5), r.flight_duration, 108) AS flight_duration,
            dep.airport_code AS departs_code,
            arr.airport_code AS arrives_code,
            af.aircraft_model,
            af.airfleet_id,
            fst.flight_status_name
        FROM Flight f
        INNER JOIN FlightSchedule fs ON f.flight_schedule_id = fs.flight_schedule_id
        INNER JOIN Route r ON fs.route_id = r.route_id
        INNER JOIN Airfleet af ON r.airfleet_id = af.airfleet_id
        INNER JOIN Airport dep ON r.departs_airport_id = dep.airport_id
        INNER JOIN Airport arr ON r.arrives_airport_id = arr.airport_id
        INNER JOIN FlightStatus fst ON f.flight_status_id = fst.flight_status_id
        WHERE r.route_id = :route_id
          AND fst.flight_status_name IN ('Auto-scheduled', 'Scheduled')
        ORDER BY f.departs_datetime
    """)
    return db.execute(sql, {"route_id": route_id}).mappings().all()


def confirm_flights(db: Session, flight_ids: list[int]) -> int:
    scheduled_id = get_status_id_by_name(db, "Scheduled")
    auto_id = get_status_id_by_name(db, "Auto-scheduled")
    
    count = 0
    for flight_id in flight_ids:
        result = db.execute(text("""
            UPDATE Flight
            SET flight_status_id = :scheduled_id
            WHERE flight_id = :flight_id
              AND flight_status_id = :auto_id
        """), {
            "scheduled_id": scheduled_id,
            "flight_id": flight_id,
            "auto_id": auto_id,
        })
        count += result.rowcount
    
    db.commit()
    return count


def update_flight_classes(
    db: Session,
    flight_id: int,
    class_ids: list[int],
) -> None:
    sql_existing = text("""
        SELECT class_id FROM FlightClass WHERE flight_id = :flight_id
    """)
    existing = {r[0] for r in db.execute(
        sql_existing, {"flight_id": flight_id}).fetchall()}

    for class_id in existing:
        if class_id not in class_ids:
            has_bookings = db.execute(text("""
                SELECT COUNT(*) FROM FlightClass fc
                INNER JOIN FlightPrice fp ON fc.flight_class_id = fp.flight_class_id
                INNER JOIN BookingItem bi ON bi.flight_price_id = fp.flight_price_id
                WHERE fc.flight_id = :flight_id AND fc.class_id = :class_id
            """), {"flight_id": flight_id, "class_id": class_id}).scalar()

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

    db.commit()


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
                  ON bb.baggage_pricing_in_flight_id = bpif.baggage_pricing_in_flight_id
          )
    """), {"flight_id": flight_id})

    find_fc_sql = text("""
        SELECT class_id, flight_class_id 
        FROM FlightClass 
        WHERE flight_id = :flight_id
    """)
    flight_classes = db.execute(
        find_fc_sql, {"flight_id": flight_id}).mappings().all()
    class_map = {row["class_id"]: row["flight_class_id"] 
                 for row in flight_classes}

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
                "flight_id": flight_id,
                "rule_id": opt["baggage_pricing_rule_id"],
                "flight_class_id": flight_class_id,
                "price": opt["price"],
            })

    db.commit()


def cancel_flight(db: Session, flight_id: int) -> bool:
    status_id = get_status_id_by_name(db, "Cancelled")
    if not status_id:
        return False
    
    sql = text("""
        UPDATE Flight 
        SET flight_status_id = :status_id 
        WHERE flight_id = :flight_id
    """)
    db.execute(sql, {"status_id": status_id, "flight_id": flight_id})
    db.commit()
    return True

def update_flight_times(db: Session, flight_id: int, departs_datetime: str, arrives_datetime: str):
    sql = text("""
        UPDATE Flight 
        SET departs_datetime = :dep, arrives_datetime = :arr
        WHERE flight_id = :flight_id
    """)
    db.execute(sql, {
        "dep": departs_datetime,
        "arr": arrives_datetime,
        "flight_id": flight_id
    })
    db.commit()


