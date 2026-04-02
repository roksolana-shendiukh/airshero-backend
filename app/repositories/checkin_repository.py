from sqlalchemy.orm import Session
from sqlalchemy import text


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


def get_active_flights_for_agent(db: Session, airport_id: int) -> list:
    sql = text("""
        SELECT
            fo.flight_operation_id,
            fo.flight_id,
            r.flight_number,
            f.departs_datetime,
            f.arrives_datetime,
            ap_dep.airport_code  AS departs_airport_code,
            ap_dep.airport_name  AS departs_airport_name,
            ap_arr.airport_code  AS arrives_airport_code,
            ap_arr.airport_name  AS arrives_airport_name,
            fos.flight_operation_status_name AS status,
            g.gate_code,
            fo.boarding_start_time,
            fo.boarding_end_time
        FROM FlightOperation fo
        JOIN Flight f              ON f.flight_id              = fo.flight_id
        JOIN FlightSchedule fs     ON fs.flight_schedule_id    = f.flight_schedule_id
        JOIN Route r               ON r.route_id               = fs.route_id
        JOIN Airport ap_dep        ON ap_dep.airport_id        = r.departs_airport_id
        JOIN Airport ap_arr        ON ap_arr.airport_id        = r.arrives_airport_id
        JOIN FlightOperationStatus fos ON fos.flight_operation_status_id = fo.flight_operation_status_id
        JOIN Gate g                ON g.gate_id                = fo.gate_id
        JOIN Terminal t            ON t.terminal_id            = g.terminal_id
        WHERE ap_dep.airport_id = :airport_id
            AND fos.flight_operation_status_name IN ('Boarding', 'Scheduled', 'Delayed')
        ORDER BY f.departs_datetime
    """)

    rows = db.execute(sql, {"airport_id": airport_id}).mappings().all()

    return [
        {
            "flightOperationId": r["flight_operation_id"],
            "flightId":          r["flight_id"],
            "flightNumber":      r["flight_number"],
            "departsDatetime":   str(r["departs_datetime"]),
            "arrivesDatetime":   str(r["arrives_datetime"]),
            "departsAirport":    r["departs_airport_code"],
            "arrivesAirport":    r["arrives_airport_code"],
            "arrivesAirportName": r["arrives_airport_name"],
            "status":            r["status"],
            "gateCode":          r["gate_code"],
            "boardingStartTime": str(r["boarding_start_time"]) if r["boarding_start_time"] else None,
            "boardingEndTime":   str(r["boarding_end_time"])   if r["boarding_end_time"]   else None,
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
        JOIN [FlightPrice] fp ON fp.[flight_price_id] = bi.[flight_price_id]
        JOIN [FlightClass] fc ON fc.[flight_class_id] = fp.[flight_class_id]
        JOIN [Flight] f ON f.[flight_id] = fc.[flight_id]
        JOIN [FlightSchedule] fs ON fs.[flight_schedule_id] = f.[flight_schedule_id]
        JOIN [Route] r ON r.[route_id] = fs.[route_id]
        WHERE pd.[document_number] LIKE '%' + :q + '%'
          AND r.[flight_number] = :flight_num
          AND CAST(f.[departs_datetime] AS DATE) = :departs_date
    """)
    
    result = db.execute(sql, {
        "q": f"{q}%", 
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


def get_checked_baggage_weight(db: Session, flight_operation_id: int) -> float:
    sql = text("""
        SELECT ISNULL(SUM(bu.baggage_unit_weight_kg), 0) AS total_weight
        FROM FlightOperation fo
        JOIN BoardingPass bp ON bp.flight_operation_id = fo.flight_operation_id
        JOIN BaggageUnit bu  ON bu.boarding_pass_id    = bp.boarding_pass_id
        JOIN BaggageType bt  ON bt.baggage_type_id     = bu.baggage_type_id
        WHERE fo.flight_operation_id = :flight_operation_id
          AND bt.baggage_type_name != 'Carry-on baggage'
    """)
    result = db.execute(
        sql, {"flight_operation_id": flight_operation_id}
    ).mappings().first()
    return float(result["total_weight"]) if result else 0.0


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