from sqlalchemy.orm import Session
from sqlalchemy import text


def get_overview_flights(
    db: Session,
    airline_id: int,
    mode: str = "day",
    date: str | None = None,
    month: int | None = None,
    year: int | None = None,
    status: str | None = None,
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
        INNER JOIN FlightClass fc       ON f.flight_id = fc.flight_id
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

