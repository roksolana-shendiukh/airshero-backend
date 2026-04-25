from sqlalchemy.orm import Session
from sqlalchemy import text
import random
import string

def get_passenger_booking(
    db: Session,
    document_number: str,
    flight_number: str,
    departs_date: str,
):
    result = db.execute(
        text("EXEC SP_GetPassengerBooking :document_number, :flight_number, :departs_date"),
        {
            "document_number": document_number,
            "flight_number":   flight_number,
            "departs_date":    departs_date,
        },
    )
    return result.mappings().all()


def get_seat_map(db: Session, flight_operation_id: int) -> dict | None:
    sql = text("""
        SELECT
            seat_layout_id,
            seat_position,
            seat_layout_rows,
            seat_layout_columns,
            class_id,
            class_name,
            seat_type_id,
            seat_type_name,
            is_emergency_exit,
            is_occupied
        FROM FN_GetAvailableSeats(:flight_operation_id)
        ORDER BY class_id, seat_layout_rows, seat_layout_columns
    """)

    rows = db.execute(
        sql, {"flight_operation_id": flight_operation_id}
    ).mappings().all()

    if not rows:
        return None

    return {
        "flightOperationId": flight_operation_id,
        "seats": [
            {
                "seatLayoutId":    r["seat_layout_id"],
                "seatPosition":    r["seat_position"],
                "row":             r["seat_layout_rows"],
                "column":          r["seat_layout_columns"],
                "classId":         r["class_id"],
                "className":       r["class_name"],
                "seatTypeId":      r["seat_type_id"],
                "seatTypeName":    r["seat_type_name"],
                "isEmergencyExit": bool(r["is_emergency_exit"]),
                "isOccupied":      bool(r["is_occupied"]),
            }
            for r in rows
        ],
    }


def get_active_flights_for_agent(db: Session, airport_id: int, airline_id: int | None = None) -> list:
    sql = text("""
        SELECT
            fo.flight_operation_id,
            fo.flight_id,
            r.flight_number,
            f.departs_datetime,
            f.arrives_datetime,
            c_dep.country_id AS departs_country_id,
            c_arr.country_id AS arrives_country_id,
            ap_dep.airport_code  AS departs_airport_code,
            ap_dep.airport_name  AS departs_airport_name,
            ap_arr.airport_code  AS arrives_airport_code,
            ap_arr.airport_name  AS arrives_airport_name,
            ISNULL(fos.flight_operation_status_name, 'Scheduled') AS status,
            ISNULL(g.gate_code, '—') AS gate_code,
            fo.boarding_start_time,
            fo.boarding_end_time
        FROM Flight f
        JOIN FlightSchedule fs     ON fs.flight_schedule_id    = f.flight_schedule_id
        JOIN Route r               ON r.route_id               = fs.route_id
        JOIN Airport ap_dep        ON ap_dep.airport_id        = r.departs_airport_id
        JOIN Airport ap_arr        ON ap_arr.airport_id        = r.arrives_airport_id
        JOIN City c_dep            ON c_dep.city_id            = ap_dep.city_id
        JOIN City c_arr            ON c_arr.city_id            = ap_arr.city_id
        LEFT JOIN FlightOperation fo ON fo.flight_id = f.flight_id
        LEFT JOIN FlightOperationStatus fos ON fos.flight_operation_status_id = fo.flight_operation_status_id
        LEFT JOIN Gate g           ON g.gate_id = fo.gate_id
        LEFT JOIN Terminal t       ON t.terminal_id = g.terminal_id
        WHERE ap_dep.airport_id = :airport_id
            AND f.departs_datetime >= GETDATE()
            AND f.departs_datetime <= DATEADD(hour, 12, GETDATE())
            AND (
                fos.flight_operation_status_name IN ('Waiting', 'Boarding')
                OR fo.flight_operation_id IS NULL
            )
        ORDER BY f.departs_datetime
    """)

    rows = db.execute(sql, {"airport_id": airport_id, "airline_id": airline_id}).mappings().all()
    print(f">>> active flights rows: {len(rows)}")
    return [
        {
            "flightOperationId":  r["flight_operation_id"],
            "flightId":           r["flight_id"],
            "flightNumber":       r["flight_number"],
            "departsDatetime":    str(r["departs_datetime"]),
            "arrivesDatetime":    str(r["arrives_datetime"]),
            "departsCountryId":   r["departs_country_id"],
            "arrivesCountryId":   r["arrives_country_id"],
            "departsAirport":     r["departs_airport_code"],
            "arrivesAirport":     r["arrives_airport_code"],
            "arrivesAirportName": r["arrives_airport_name"],
            "status":             r["status"],
            "gateCode":           r["gate_code"],
            "boardingStartTime":  str(r["boarding_start_time"]) if r["boarding_start_time"] else None,
            "boardingEndTime":    str(r["boarding_end_time"])   if r["boarding_end_time"]   else None,
        }
        for r in rows
    ]


def get_airport_id_by_agent(db: Session, agent_id: int) -> int | None:
    sql = text("""
        SELECT airport_id
        FROM CheckInAgent
        WHERE checkin_agent_id = :agent_id
    """)
    result = db.execute(sql, {"agent_id": agent_id}).mappings().first()
    return result["airport_id"] if result else None


def get_suggestions_for_flight(db: Session, q: str, flight_num: str, departs_date: str):
    sql = text("""
        SELECT DISTINCT 
            pd.[document_number] as document_number, 
            p.[passenger_first_name] as first_name, 
            p.[passenger_last_name] as last_name
        FROM [PassengerDocument] pd
        JOIN [Passenger] p ON p.[passenger_id] = pd.[passenger_id]
        JOIN [BookingItem] bi ON bi.[passenger_document_id] = pd.[passenger_document_id]
        JOIN [Booking] b ON b.[booking_id] = bi.[booking_id]
        JOIN [BookingStatus] bs ON bs.[booking_status_id] = b.[booking_status_id]
        JOIN [FlightPrice] fp ON fp.[flight_price_id] = bi.[flight_price_id]
        JOIN [FlightClass] fc ON fc.[flight_class_id] = fp.[flight_class_id]
        JOIN [Flight] f ON f.[flight_id] = fc.[flight_id]
        JOIN [FlightSchedule] fs ON fs.[flight_schedule_id] = f.[flight_schedule_id]
        JOIN [Route] r ON r.[route_id] = fs.[route_id]
        LEFT JOIN [BoardingPass] bp ON bp.[booking_item_id] = bi.[booking_item_id]
            AND bp.[flight_operation_id] = (
                SELECT TOP 1 fo.flight_operation_id 
                FROM FlightOperation fo
                JOIN Flight f2 ON f2.flight_id = fo.flight_id
                JOIN FlightSchedule fs2 ON fs2.flight_schedule_id = f2.flight_schedule_id
                JOIN Route r2 ON r2.route_id = fs2.route_id
                WHERE r2.flight_number = :flight_num
                AND CAST(f2.departs_datetime AS DATE) = :departs_date
                AND fo.flight_operation_status_id NOT IN (
                    SELECT flight_operation_status_id FROM FlightOperationStatus 
                    WHERE flight_operation_status_name IN ('Cancelled', 'Completed')
                )
            )
        WHERE pd.[document_number] LIKE :q + '%'
        AND r.[flight_number] = :flight_num
        AND CAST(f.[departs_datetime] AS DATE) = :departs_date
        AND bs.[booking_status_name] = 'Confirmed'
        AND bp.[boarding_pass_id] IS NULL
    """)
    
    result = db.execute(sql, {
        "q": q, 
        "flight_num": flight_num, 
        "departs_date": departs_date
    })
    return result.mappings().all()


def get_baggage_info(db: Session, booking_item_id: int) -> dict | None:
    sql = text("""
        SELECT
            bi.booking_item_id,
            ISNULL(boi.baggage_quantity, 0) as baggage_quantity,
            ISNULL(bpr.baggage_max_weight, 0) as baggage_max_weight,
            ISNULL(bt.baggage_type_id, 0) as baggage_type_id,
            ISNULL(bt.baggage_type_name, 'No baggage') as baggage_type_name,
            fc.class_id
        FROM BookingItem bi
        INNER JOIN FlightPrice fp ON fp.flight_price_id = bi.flight_price_id
        INNER JOIN FlightClass fc ON fc.flight_class_id = fp.flight_class_id
        LEFT JOIN BaggageOptionInFlight boi ON boi.booking_item_id = bi.booking_item_id
        LEFT JOIN BaggagePricingInFlight bpif ON bpif.baggage_pricing_in_flight_id = boi.baggage_pricing_in_flight_id
        LEFT JOIN BaggagePricingRule bpr ON bpr.baggage_pricing_rule_id = bpif.baggage_pricing_rule_id
        LEFT JOIN BaggageType bt ON bt.baggage_type_id = bpr.baggage_type_id
        WHERE bi.booking_item_id = :booking_item_id
    """)

    row = db.execute(sql, {"booking_item_id": booking_item_id}).mappings().first()
    if not row:
        return None

    return {
        "bookingItemId":      row["booking_item_id"],
        "baggageQuantity":    row["baggage_quantity"],
        "baggageMaxWeight":   float(row["baggage_max_weight"]),
        "baggageTypeId":      row["baggage_type_id"],
        "baggageTypeName":    row["baggage_type_name"],
        "classId":            row["class_id"],
    }


def get_baggage_types(db: Session) -> list:
    sql = text("""
        SELECT baggage_type_id, baggage_type_name
        FROM BaggageType
        WHERE baggage_type_name != 'Carry-on baggage'
        ORDER BY baggage_type_id
    """)
    rows = db.execute(sql).mappings().all()
    return [
        {
            "baggageTypeId":   r["baggage_type_id"],
            "baggageTypeName": r["baggage_type_name"],
        }
        for r in rows
    ]

def get_checked_baggage_weight(db: Session, flight_operation_id: int):
    weight_sql = text("""
        SELECT dbo.FN_GetCheckedBaggageWeight(:flight_operation_id) AS total_weight
    """)
    capacity_sql = text("""
        SELECT a.baggage_capacity
        FROM FlightOperation fo
        JOIN Airfleet a ON a.airfleet_id = fo.airfleet_id
        WHERE fo.flight_operation_id = :flight_operation_id
    """)
    
    weight   = db.execute(weight_sql,   {"flight_operation_id": flight_operation_id}).mappings().first()
    capacity = db.execute(capacity_sql, {"flight_operation_id": flight_operation_id}).mappings().first()

    return {
        "totalCheckedWeightKg": float(weight["total_weight"])          if weight   else 0.0,
        "baggageCapacityKg":    float(capacity["baggage_capacity"])    if capacity else 0.0,
    }


def get_flight_info_for_booking_item(db: Session, booking_item_id: int) -> dict | None:
    sql = text("""
        SELECT fc.flight_id, fc.flight_class_id
        FROM BookingItem bi
        INNER JOIN FlightPrice fp ON bi.flight_price_id = fp.flight_price_id
        INNER JOIN FlightClass fc ON fp.flight_class_id = fc.flight_class_id
        WHERE bi.booking_item_id = :booking_item_id
    """)
    result = db.execute(sql, {"booking_item_id": booking_item_id}).mappings().first()
    return dict(result) if result else None


def get_booking_baggage_allowance(db: Session, booking_item_id: int) -> dict | None:
    sql = text("""
        SELECT
            boif.baggage_quantity,
            bpif.baggage_price,
            bpr.baggage_max_weight,
            bpr.overweight_fee_per_kg,
            bt.baggage_type_id,
            bt.baggage_type_name
        FROM BaggageOptionInFlight boif
        INNER JOIN BaggagePricingInFlight bpif ON boif.baggage_pricing_in_flight_id = bpif.baggage_pricing_in_flight_id
        INNER JOIN BaggagePricingRule bpr ON bpif.baggage_pricing_rule_id = bpr.baggage_pricing_rule_id
        INNER JOIN BaggageType bt ON bpr.baggage_type_id = bt.baggage_type_id
        WHERE boif.booking_item_id = :booking_item_id
    """)
    result = db.execute(sql, {"booking_item_id": booking_item_id}).mappings().first()
    return dict(result) if result else None


def get_flight_class_baggage_rules(db: Session, flight_class_id: int) -> list[dict]:
    sql = text("""
        SELECT
            bpif.baggage_price,
            bpr.baggage_max_weight,
            bpr.baggage_dimension,
            bpr.overweight_fee_per_kg,
            bt.baggage_type_id,
            bt.baggage_type_name
        FROM BaggagePricingInFlight bpif
        INNER JOIN BaggagePricingRule bpr ON bpif.baggage_pricing_rule_id = bpr.baggage_pricing_rule_id
        INNER JOIN BaggageType bt ON bpr.baggage_type_id = bt.baggage_type_id
        WHERE bpif.flight_class_id = :flight_class_id
        ORDER BY bpr.baggage_max_weight ASC
    """)
    return [dict(row) for row in db.execute(sql, {"flight_class_id": flight_class_id}).mappings().all()]


def get_payment_methods(db: Session) -> list:
    sql = text("""
        SELECT payment_method_id, payment_method_name
        FROM PaymentMethod
        ORDER BY payment_method_id
    """)
    rows = db.execute(sql).mappings().all()
    return [
        {
            "paymentMethodId":   r["payment_method_id"],
            "paymentMethodName": r["payment_method_name"],
        }
        for r in rows
    ]


def issue_boarding_pass_with_baggage(
    db: Session,
    booking_item_id: int,
    seat_layout_id: int,
    flight_operation_id: int,
    checkin_agent_id: int,
    bags: list[dict],
    payment_method_id: int | None,
    total_surcharge: float,
    status: str,
) -> dict:
    existing_sql = text("""
        SELECT boarding_pass_id, boarding_pass_ticket_number
        FROM BoardingPass
        WHERE booking_item_id = :booking_item_id
        AND flight_operation_id = :flight_operation_id
    """)
    existing = db.execute(existing_sql, {
        "booking_item_id": booking_item_id,
        "flight_operation_id": flight_operation_id,
    }).mappings().first()
    if existing:
        raise ValueError(f"Passenger already checked in. Boarding pass: {existing['boarding_pass_ticket_number']}")

    ticket_number = 'BP' + ''.join(random.choices(string.digits, k=8))

    bp_sql = text("""
        INSERT INTO BoardingPass (
            checkin_agent_id, seat_layout_id, booking_item_id,
            flight_operation_id, boarding_pass_issue_date_time,
            boarding_pass_ticket_number
        )
        OUTPUT INSERTED.boarding_pass_id, INSERTED.boarding_pass_ticket_number
        VALUES (
            :agent_id, :seat_layout_id, :booking_item_id,
            :flight_operation_id, GETDATE(), :ticket_number
        )
    """)
    bp = db.execute(bp_sql, {
        "agent_id":            checkin_agent_id,
        "seat_layout_id":      seat_layout_id,
        "booking_item_id":     booking_item_id,
        "flight_operation_id": flight_operation_id,
        "ticket_number":       ticket_number,
    }).mappings().first()

    boarding_pass_id = bp["boarding_pass_id"]

    carryon_sql = text("""
        SELECT baggage_type_id FROM BaggageType
        WHERE baggage_type_name = 'Carry-on baggage'
    """)
    carryon = db.execute(carryon_sql).mappings().first()
    carryon_type_id = carryon["baggage_type_id"] if carryon else None

    bag_details = []

    if carryon_type_id is not None:
        carryon_tracking = 'TK' + ''.join(random.choices(string.digits, k=10))
        carryon_sql = text("""
            INSERT INTO BaggageUnit (
                boarding_pass_id, baggage_type_id,
                baggage_unit_tracking_number, baggage_unit_weight_kg
            )
            OUTPUT INSERTED.baggage_unit_id
            VALUES (
                :boarding_pass_id, :baggage_type_id,
                :tracking, :weight
            )
        """)
        db.execute(carryon_sql, {
            "boarding_pass_id": boarding_pass_id,
            "baggage_type_id":  carryon_type_id,
            "tracking":         carryon_tracking,
            "weight":           0,
        }).mappings().first()
        bag_details.append({
            "trackingNumber": carryon_tracking,
            "baggageTypeId":  carryon_type_id,
            "baggageTypeName": "Carry-on baggage",
            "weightKg":       0.0,
        })

    bag_ids = []
    for bag in bags:
        tracking = 'TK' + ''.join(random.choices(string.digits, k=10))
        bu_sql = text("""
            INSERT INTO BaggageUnit (
                boarding_pass_id, baggage_type_id,
                baggage_unit_tracking_number, baggage_unit_weight_kg
            )
            OUTPUT INSERTED.baggage_unit_id
            VALUES (
                :boarding_pass_id, :baggage_type_id,
                :tracking, :weight
            )
        """)
        bu = db.execute(bu_sql, {
            "boarding_pass_id": boarding_pass_id,
            "baggage_type_id":  bag["baggage_type_id"],
            "tracking":         tracking,
            "weight":           bag["baggage_unit_weight_kg"],
        }).mappings().first()
        bag_ids.append(bu["baggage_unit_id"])

        type_name_sql = text("""
            SELECT baggage_type_name FROM BaggageType
            WHERE baggage_type_id = :type_id
        """)
        type_row = db.execute(type_name_sql, {"type_id": bag["baggage_type_id"]}).mappings().first()

        bag_details.append({
            "trackingNumber":  tracking,
            "baggageTypeId":   bag["baggage_type_id"],
            "baggageTypeName": type_row["baggage_type_name"] if type_row else "—",
            "weightKg":        float(bag["baggage_unit_weight_kg"]),
        })

    checkin_payment_id = None
    if total_surcharge > 0 and payment_method_id:
        pay_sql = text("""
            INSERT INTO CheckinInPayment (
                payment_status_id, payment_method_id,
                checkin_payment_date_time, checkin_payment_amount
            )
            OUTPUT INSERTED.checkin_payment_id
            VALUES (
                (SELECT payment_status_id FROM PaymentStatus WHERE payment_status_name = :status),
                :method_id, GETDATE(), :amount
            )
        """)
        pay = db.execute(pay_sql, {
            "method_id": payment_method_id,
            "amount":    total_surcharge,
            "status":    status,
        }).mappings().first()
        checkin_payment_id = pay["checkin_payment_id"]

        for bag_id in bag_ids:
            db.execute(text("""
                INSERT INTO BaggageUnitCheckInPayment (baggage_unit_id, checkin_payment_id)
                VALUES (:bag_id, :payment_id)
            """), {"bag_id": bag_id, "payment_id": checkin_payment_id})

    db.commit()

    return {
        "boardingPassId":   boarding_pass_id,
        "ticketNumber":     ticket_number,
        "checkinPaymentId": checkin_payment_id,
        "bagCount":         len(bag_details),
        "bags":             bag_details,
    }


def get_checkin_agent_by_user_id(db: Session, agent_id: int):
    sql = text("""
        SELECT checkin_agent_id
        FROM CheckInAgent
        WHERE checkin_agent_id = :agent_id
    """)
    return db.execute(sql, {"agent_id": agent_id}).mappings().first()


def check_already_checked_in(db: Session, booking_item_id: int, flight_operation_id: int) -> dict | None:
    sql = text("""
        SELECT bp.boarding_pass_id, bp.boarding_pass_ticket_number
        FROM BoardingPass bp
        WHERE bp.booking_item_id = :booking_item_id
        AND bp.flight_operation_id = :flight_operation_id
    """)
    row = db.execute(sql, {
        "booking_item_id": booking_item_id,
        "flight_operation_id": flight_operation_id,
    }).mappings().first()
    return dict(row) if row else None


def get_boarding_stats(db: Session, flight_operation_id: int) -> dict:
    sql = text("""
        SELECT
            COUNT(DISTINCT bi.booking_item_id) AS total_passengers,
            COUNT(DISTINCT bp.boarding_pass_id) AS checked_in
        FROM FlightClass fc
        JOIN FlightPrice fp ON fp.flight_class_id = fc.flight_class_id
        JOIN BookingItem bi ON bi.flight_price_id = fp.flight_price_id
        JOIN Booking b ON b.booking_id = bi.booking_id
        JOIN BookingStatus bs ON bs.booking_status_id = b.booking_status_id
        LEFT JOIN BoardingPass bp ON bp.booking_item_id = bi.booking_item_id
            AND bp.flight_operation_id = :flight_operation_id
        WHERE fc.flight_id = (
            SELECT flight_id FROM FlightOperation
            WHERE flight_operation_id = :flight_operation_id
        )
        AND bs.booking_status_name = 'Confirmed'
    """)
    row = db.execute(sql, {"flight_operation_id": flight_operation_id}).mappings().first()
    total      = row["total_passengers"] if row else 0
    checked_in = row["checked_in"]       if row else 0
    return {
        "totalPassengers": total,
        "checkedIn":       checked_in,
        "remaining":       total - checked_in,
    }


def get_recently_checked_in(db: Session, flight_operation_id: int) -> list:
    sql = text("""
        SELECT 
            bp.boarding_pass_id,
            bp.boarding_pass_ticket_number,
            p.passenger_first_name,
            p.passenger_last_name,
            CAST(sl.seat_layout_rows AS VARCHAR) + sl.seat_layout_columns AS seat_position,
            c.class_name,
            bp.boarding_pass_issue_date_time,
            bp.flight_operation_id,
            COUNT(bu.baggage_unit_id) AS bag_count
        FROM BoardingPass bp
        JOIN BookingItem bi ON bi.booking_item_id = bp.booking_item_id
        JOIN PassengerDocument pd ON pd.passenger_document_id = bi.passenger_document_id
        JOIN Passenger p ON p.passenger_id = pd.passenger_id
        JOIN SeatLayout sl ON sl.seat_layout_id = bp.seat_layout_id
        JOIN FlightPrice fp ON fp.flight_price_id = bi.flight_price_id
        JOIN FlightClass fc ON fc.flight_class_id = fp.flight_class_id
        JOIN Class c ON c.class_id = fc.class_id
        LEFT JOIN BaggageUnit bu ON bu.boarding_pass_id = bp.boarding_pass_id
        WHERE bp.flight_operation_id = :flight_operation_id
        GROUP BY
            bp.boarding_pass_id,
            bp.boarding_pass_ticket_number,
            p.passenger_first_name,
            p.passenger_last_name,
            sl.seat_layout_rows,
            sl.seat_layout_columns,
            c.class_name,
            bp.boarding_pass_issue_date_time,
            bp.flight_operation_id
        ORDER BY bp.boarding_pass_issue_date_time DESC
    """)
    rows = db.execute(sql, {
        "flight_operation_id": flight_operation_id,
    }).mappings().all()
    return [
        {
            "boardingPassId":    r["boarding_pass_id"],
            "ticketNumber":      r["boarding_pass_ticket_number"],
            "passengerName":     f"{r['passenger_first_name']} {r['passenger_last_name']}",
            "seat":              r["seat_position"],
            "className":         r["class_name"],
            "issuedAt":          str(r["boarding_pass_issue_date_time"]),
            "flightOperationId": r["flight_operation_id"],
            "bagCount":          r["bag_count"],
        }
        for r in rows
    ]


def get_boarding_pass_details(db: Session, boarding_pass_id: int) -> dict | None:
    sql = text("""
        SELECT
            bp.boarding_pass_ticket_number,
            p.passenger_first_name,
            p.passenger_last_name,
            r.flight_number,
            c.class_name,
            CAST(sl.seat_layout_rows AS VARCHAR) + sl.seat_layout_columns AS seat_position,
            f.departs_datetime,
            f.arrives_datetime,
            ap_dep.airport_code AS departs_airport,
            ap_arr.airport_code AS arrives_airport,
            g.gate_code,
            COUNT(bu.baggage_unit_id) AS bag_count
        FROM BoardingPass bp
        JOIN BookingItem bi ON bi.booking_item_id = bp.booking_item_id
        JOIN PassengerDocument pd ON pd.passenger_document_id = bi.passenger_document_id
        JOIN Passenger p ON p.passenger_id = pd.passenger_id
        JOIN SeatLayout sl ON sl.seat_layout_id = bp.seat_layout_id
        JOIN FlightPrice fp ON fp.flight_price_id = bi.flight_price_id
        JOIN FlightClass fc ON fc.flight_class_id = fp.flight_class_id
        JOIN Class c ON c.class_id = fc.class_id
        JOIN FlightOperation fo ON fo.flight_operation_id = bp.flight_operation_id
        JOIN Flight f ON f.flight_id = fo.flight_id
        JOIN FlightSchedule fs ON fs.flight_schedule_id = f.flight_schedule_id
        JOIN Route r ON r.route_id = fs.route_id
        JOIN Airport ap_dep ON ap_dep.airport_id = r.departs_airport_id
        JOIN Airport ap_arr ON ap_arr.airport_id = r.arrives_airport_id
        JOIN Gate g ON g.gate_id = fo.gate_id
        LEFT JOIN BaggageUnit bu ON bu.boarding_pass_id = bp.boarding_pass_id
        WHERE bp.boarding_pass_id = :boarding_pass_id
        GROUP BY
            bp.boarding_pass_ticket_number,
            p.passenger_first_name, p.passenger_last_name,
            r.flight_number, c.class_name,
            sl.seat_layout_rows, sl.seat_layout_columns,
            f.departs_datetime, f.arrives_datetime,
            ap_dep.airport_code, ap_arr.airport_code,
            g.gate_code
    """)
    row = db.execute(sql, {"boarding_pass_id": boarding_pass_id}).mappings().first()
    if not row:
        return None
    return {
        "ticketNumber":   row["boarding_pass_ticket_number"],
        "passengerName":  f"{row['passenger_first_name']} {row['passenger_last_name']}",
        "flightNumber":   row["flight_number"],
        "flightClass":    row["class_name"],
        "seat":           row["seat_position"],
        "departsTime":    str(row["departs_datetime"]),
        "arrivesTime":    str(row["arrives_datetime"]),
        "departsAirport": row["departs_airport"],
        "arrivesAirport": row["arrives_airport"],
        "gate":           row["gate_code"],
        "bagCount":       row["bag_count"],
    }


def get_boarding_passes_history(
    db: Session,
    agent_id: int,
    search: str | None = None,
    route_city: str | None = None,
    class_name: str | None = None,
    date_filter: str | None = 'today',
    skip: int = 0,
    limit: int = 50,
) -> list:
    date_condition = ""
    if date_filter == 'today':
        date_condition = "AND CAST(f.departs_datetime AS DATE) = CAST(GETDATE() AS DATE)"
    elif date_filter == 'this_week':
        date_condition = "AND f.departs_datetime >= DATEADD(DAY, 1 - DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE)) AND f.departs_datetime < DATEADD(DAY, 8 - DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE))"
    elif date_filter == 'this_month':
        date_condition = "AND MONTH(f.departs_datetime) = MONTH(GETDATE()) AND YEAR(f.departs_datetime) = YEAR(GETDATE())"

    search_condition = ""
    if search:
        search_condition = """
            AND (
                bp.boarding_pass_ticket_number LIKE :search
                OR p.passenger_first_name + ' ' + p.passenger_last_name LIKE :search
                OR r.flight_number LIKE :search
            )
        """

    route_condition = ""
    if route_city:
        route_condition = """
            AND (
                dep_city.city_name = :route_city
                OR arr_city.city_name = :route_city
            )
        """

    class_condition = ""
    if class_name:
        class_condition = "AND c.class_name = :class_name"

    sql = text(f"""
        SELECT
            bp.boarding_pass_id,
            bp.boarding_pass_ticket_number,
            bp.boarding_pass_issue_date_time,
            p.passenger_first_name,
            p.passenger_last_name,
            r.flight_number,
            f.departs_datetime,
            f.arrives_datetime,
            ap_dep.airport_code AS departs_airport,
            ap_arr.airport_code AS arrives_airport,
            dep_city.city_name AS departs_city,
            arr_city.city_name AS arrives_city,
            c.class_name,
            CAST(sl.seat_layout_rows AS VARCHAR) + sl.seat_layout_columns AS seat_position,
            COUNT(bu.baggage_unit_id) AS bag_count
        FROM BoardingPass bp
        JOIN CheckInAgent ca ON ca.checkin_agent_id = bp.checkin_agent_id
        JOIN BookingItem bi ON bi.booking_item_id = bp.booking_item_id
        JOIN PassengerDocument pd ON pd.passenger_document_id = bi.passenger_document_id
        JOIN Passenger p ON p.passenger_id = pd.passenger_id
        JOIN SeatLayout sl ON sl.seat_layout_id = bp.seat_layout_id
        JOIN FlightPrice fp ON fp.flight_price_id = bi.flight_price_id
        JOIN FlightClass fc ON fc.flight_class_id = fp.flight_class_id
        JOIN Class c ON c.class_id = fc.class_id
        JOIN FlightOperation fo ON fo.flight_operation_id = bp.flight_operation_id
        JOIN Flight f ON f.flight_id = fo.flight_id
        JOIN FlightSchedule fs ON fs.flight_schedule_id = f.flight_schedule_id
        JOIN Route r ON r.route_id = fs.route_id
        JOIN Airport ap_dep ON ap_dep.airport_id = r.departs_airport_id
        JOIN Airport ap_arr ON ap_arr.airport_id = r.arrives_airport_id
        JOIN City dep_city ON dep_city.city_id = ap_dep.city_id
        JOIN City arr_city ON arr_city.city_id = ap_arr.city_id
        LEFT JOIN BaggageUnit bu ON bu.boarding_pass_id = bp.boarding_pass_id
        WHERE ca.checkin_agent_id = :agent_id
        {date_condition}
        {search_condition}
        {route_condition}
        {class_condition}
        GROUP BY
            bp.boarding_pass_id,
            bp.boarding_pass_ticket_number,
            bp.boarding_pass_issue_date_time,
            p.passenger_first_name, p.passenger_last_name,
            r.flight_number,
            f.departs_datetime, f.arrives_datetime,
            ap_dep.airport_code, ap_arr.airport_code,
            dep_city.city_name, arr_city.city_name,
            c.class_name,
            sl.seat_layout_rows, sl.seat_layout_columns
        ORDER BY bp.boarding_pass_issue_date_time DESC
        OFFSET :skip ROWS FETCH NEXT :limit ROWS ONLY
    """)

    params: dict = {"agent_id": agent_id, "skip": skip, "limit": limit}
    if search:
        params["search"] = f"%{search}%"
    if route_city:
        params["route_city"] = route_city
    if class_name:
        params["class_name"] = class_name

    rows = db.execute(sql, params).mappings().all()
    return [
        {
            "boardingPassId":  r["boarding_pass_id"],
            "ticketNumber":    r["boarding_pass_ticket_number"],
            "issuedAt":        str(r["boarding_pass_issue_date_time"]),
            "passengerName":   f"{r['passenger_first_name']} {r['passenger_last_name']}",
            "flightNumber":    r["flight_number"],
            "departsDatetime": str(r["departs_datetime"]),
            "arrivesDatetime": str(r["arrives_datetime"]),
            "departsAirport":  r["departs_airport"],
            "arrivesAirport":  r["arrives_airport"],
            "departsCity":     r["departs_city"],
            "arrivesCity":     r["arrives_city"],
            "className":       r["class_name"],
            "seat":            r["seat_position"],
            "bagCount":        r["bag_count"],
        }
        for r in rows
    ]


def get_baggage_units(db: Session, boarding_pass_id: int) -> list:
    sql = text("""
        SELECT
            bu.baggage_unit_id,
            bu.baggage_unit_tracking_number,
            bu.baggage_unit_weight_kg,
            bt.baggage_type_name
        FROM BaggageUnit bu
        JOIN BaggageType bt ON bt.baggage_type_id = bu.baggage_type_id
        WHERE bu.boarding_pass_id = :boarding_pass_id
        ORDER BY bu.baggage_unit_id
    """)
    rows = db.execute(sql, {"boarding_pass_id": boarding_pass_id}).mappings().all()
    return [
        {
            "baggageUnitId":     r["baggage_unit_id"],
            "trackingNumber":    r["baggage_unit_tracking_number"],
            "weightKg":          float(r["baggage_unit_weight_kg"]),
            "baggageTypeName":   r["baggage_type_name"],
        }
        for r in rows
    ]


def get_boarding_pass_classes(db: Session, agent_id: int) -> list:
    sql = text("""
        SELECT DISTINCT c.class_name
        FROM BoardingPass bp
        JOIN CheckInAgent ca ON ca.checkin_agent_id = bp.checkin_agent_id
        JOIN BookingItem bi ON bi.booking_item_id = bp.booking_item_id
        JOIN FlightPrice fp ON fp.flight_price_id = bi.flight_price_id
        JOIN FlightClass fc ON fc.flight_class_id = fp.flight_class_id
        JOIN Class c ON c.class_id = fc.class_id
        WHERE ca.checkin_agent_id = :agent_id
        ORDER BY c.class_name
    """)
    rows = db.execute(sql, {"agent_id": agent_id}).fetchall()
    return [r[0] for r in rows]

def get_boarding_pass_cities(db: Session, agent_id: int) -> list:
    sql = text("""
        SELECT DISTINCT city_name FROM (
            SELECT dep_city.city_name
            FROM BoardingPass bp
            JOIN CheckInAgent ca ON ca.checkin_agent_id = bp.checkin_agent_id
            JOIN BookingItem bi ON bi.booking_item_id = bp.booking_item_id
            JOIN FlightPrice fp ON fp.flight_price_id = bi.flight_price_id
            JOIN FlightClass fc ON fc.flight_class_id = fp.flight_class_id
            JOIN FlightOperation fo ON fo.flight_operation_id = bp.flight_operation_id
            JOIN Flight f ON f.flight_id = fo.flight_id
            JOIN FlightSchedule fs ON fs.flight_schedule_id = f.flight_schedule_id
            JOIN Route r ON r.route_id = fs.route_id
            JOIN Airport ap_dep ON ap_dep.airport_id = r.departs_airport_id
            JOIN City dep_city ON dep_city.city_id = ap_dep.city_id
            WHERE ca.checkin_agent_id = :agent_id
            UNION
            SELECT arr_city.city_name
            FROM BoardingPass bp
            JOIN CheckInAgent ca ON ca.checkin_agent_id = bp.checkin_agent_id
            JOIN BookingItem bi ON bi.booking_item_id = bp.booking_item_id
            JOIN FlightPrice fp ON fp.flight_price_id = bi.flight_price_id
            JOIN FlightClass fc ON fc.flight_class_id = fp.flight_class_id
            JOIN FlightOperation fo ON fo.flight_operation_id = bp.flight_operation_id
            JOIN Flight f ON f.flight_id = fo.flight_id
            JOIN FlightSchedule fs ON fs.flight_schedule_id = f.flight_schedule_id
            JOIN Route r ON r.route_id = fs.route_id
            JOIN Airport ap_arr ON ap_arr.airport_id = r.arrives_airport_id
            JOIN City arr_city ON arr_city.city_id = ap_arr.city_id
            WHERE ca.checkin_agent_id = :agent_id
        ) cities
        ORDER BY city_name
    """)
    rows = db.execute(sql, {"agent_id": agent_id}).fetchall()
    return [r[0] for r in rows]


def reprint_boarding_pass(db: Session, boarding_pass_id: int) -> None:
    db.execute(text("""
        UPDATE BoardingPass
        SET boarding_pass_issue_date_time = GETDATE()
        WHERE boarding_pass_id = :boarding_pass_id
    """), {"boarding_pass_id": boarding_pass_id})
    db.commit()

def update_boarding_pass_seat(db: Session, boarding_pass_id: int, seat_layout_id: int) -> None:
    db.execute(text("""
        UPDATE BoardingPass
        SET seat_layout_id = :seat_layout_id,
            boarding_pass_issue_date_time = GETDATE()
        WHERE boarding_pass_id = :boarding_pass_id
    """), {"boarding_pass_id": boarding_pass_id, "seat_layout_id": seat_layout_id})
    db.commit()





