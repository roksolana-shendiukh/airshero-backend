import logging
import random
import string

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


def get_passenger_booking(
    db: Session,
    document_number: str,
    flight_number:   str,
    departs_date:    str,
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
    rows = db.execute(text("""
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
    """), {"flight_operation_id": flight_operation_id}).mappings().all()

    if not rows:
        return None

    return {
        "flight_operation_id": flight_operation_id,
        "seats": [
            {
                "seat_layout_id":  r["seat_layout_id"],
                "seat_position":   r["seat_position"],
                "row":             r["seat_layout_rows"],
                "column":          r["seat_layout_columns"],
                "class_id":        r["class_id"],
                "class_name":      r["class_name"],
                "seat_type_id":    r["seat_type_id"],
                "seat_type_name":  r["seat_type_name"],
                "is_emergency_exit": bool(r["is_emergency_exit"]),
                "is_occupied":     bool(r["is_occupied"]),
            }
            for r in rows
        ],
    }


def get_active_flights_for_agent(
    db: Session,
    airport_id:  int,
    airline_id:  int | None = None,
) -> list:
    rows = db.execute(text("""
        SELECT
            fo.flight_operation_id,
            f.flight_id,
            f.flight_number,
            sf.departs_date,
            c_dep.country_id          AS departs_country_id,
            c_arr.country_id          AS arrives_country_id,
            ap_dep.airport_code       AS departs_airport_code,
            ap_dep.airport_name       AS departs_airport_name,
            ap_arr.airport_code       AS arrives_airport_code,
            ap_arr.airport_name       AS arrives_airport_name,
            ISNULL(fos.flight_operation_status_name, 'Scheduled') AS status,
            ISNULL(g.gate_code, '—')  AS gate_code,
            fo.boarding_start_time,
            fo.boarding_end_time
        FROM Flight f
        JOIN Route r                    ON r.route_id                  = f.route_id
        JOIN ScheduledFlight sf         ON sf.flight_id                = f.flight_id
        JOIN Airport ap_dep             ON ap_dep.airport_id           = r.departs_airport_id
        JOIN Airport ap_arr             ON ap_arr.airport_id           = r.arrives_airport_id
        JOIN City c_dep                 ON c_dep.city_id               = ap_dep.city_id
        JOIN City c_arr                 ON c_arr.city_id               = ap_arr.city_id
        LEFT JOIN FlightOperation fo    ON fo.schedule_flight_id       = sf.schedule_flight_id
        LEFT JOIN FlightOperationStatus fos
                                        ON fos.flight_operation_status_id = fo.flight_operation_status_id
        LEFT JOIN Gate g                ON g.gate_id                   = fo.gate_id
        WHERE ap_dep.airport_id = :airport_id
          AND sf.departs_date >= CAST(GETDATE() AS DATE)
          AND sf.departs_date <= CAST(DATEADD(hour, 60, GETDATE()) AS DATE)
          AND (
              fos.flight_operation_status_name IN ('Waiting', 'Boarding')
              OR fo.flight_operation_id IS NULL
          )
        ORDER BY sf.departs_date
    """), {"airport_id": airport_id}).mappings().all()

    logger.debug("active flights rows: %d", len(rows))
    return [
        {
            "flight_operation_id":  r["flight_operation_id"],
            "flight_id":            r["flight_id"],
            "flight_number":        r["flight_number"],
            "departs_date":         str(r["departs_date"]),
            "departs_country_id":   r["departs_country_id"],
            "arrives_country_id":   r["arrives_country_id"],
            "departs_airport":      r["departs_airport_code"],
            "arrives_airport":      r["arrives_airport_code"],
            "arrives_airport_name": r["arrives_airport_name"],
            "status":               r["status"],
            "gate_code":            r["gate_code"],
            "boarding_start_time":  str(r["boarding_start_time"]) if r["boarding_start_time"] else None,
            "boarding_end_time":    str(r["boarding_end_time"])   if r["boarding_end_time"]   else None,
        }
        for r in rows
    ]


def get_airport_id_by_agent(db: Session, agent_id: int) -> int | None:
    result = db.execute(text("""
        SELECT airport_id FROM CheckInAgent
        WHERE checkin_agent_id = :agent_id
    """), {"agent_id": agent_id}).mappings().first()
    return result["airport_id"] if result else None


def get_suggestions_for_flight(db: Session, q: str, flight_num: str, departs_date: str):
    return db.execute(text("""
        SELECT DISTINCT
            pd.document_number,
            p.passenger_first_name  AS first_name,
            p.passenger_last_name   AS last_name
        FROM PassengerDocument pd
        JOIN Passenger p            ON p.passenger_id              = pd.passenger_id
        JOIN BookingItem bi         ON bi.passenger_document_id    = pd.passenger_document_id
        JOIN Booking b              ON b.booking_id                = bi.booking_id
        JOIN BookingStatus bs       ON bs.booking_status_id        = b.booking_status_id
        JOIN FlightPrice fp         ON fp.flight_price_id          = bi.flight_price_id
        JOIN ScheduledFlight sf     ON sf.schedule_flight_id       = fp.schedule_flight_id
        JOIN FlightClass fc         ON fc.flight_class_id          = fp.flight_class_id
        JOIN Flight f               ON f.flight_id                 = fc.flight_id
        JOIN Route r                ON r.route_id                  = f.route_id
        LEFT JOIN CheckInAgentFlightOperation cafo
                                    ON cafo.flight_operation_id    = (
                                        SELECT TOP 1 fo.flight_operation_id
                                        FROM FlightOperation fo
                                        JOIN ScheduledFlight sf2 ON sf2.schedule_flight_id = fo.schedule_flight_id
                                        JOIN Flight f2           ON f2.flight_id            = sf2.flight_id
                                        WHERE f2.flight_number = :flight_num
                                          AND sf2.departs_date  = :departs_date
                                          AND fo.flight_operation_status_id NOT IN (
                                              SELECT flight_operation_status_id
                                              FROM FlightOperationStatus
                                              WHERE flight_operation_status_name IN ('Cancelled', 'Completed')
                                          )
                                    )
        LEFT JOIN BoardingPass bp   ON bp.booking_item_id                      = bi.booking_item_id
                                    AND bp.checkInAgent_flightOperation_id     = cafo.checkInAgent_flightOperation_id
        WHERE pd.document_number LIKE :q + '%'
          AND f.flight_number       = :flight_num
          AND sf.departs_date       = :departs_date
          AND bs.booking_status_name = 'Confirmed'
          AND bp.boarding_pass_id IS NULL
    """), {"q": q, "flight_num": flight_num, "departs_date": departs_date}).mappings().all()


def get_baggage_info(db: Session, booking_item_id: int) -> dict | None:
    row = db.execute(text("""
        SELECT
            bi.booking_item_id,
            ISNULL(boi.baggage_quantity,    0)              AS baggage_quantity,
            ISNULL(bpr.baggage_max_weight,  0)              AS baggage_max_weight,
            ISNULL(bt.baggage_type_id,      0)              AS baggage_type_id,
            ISNULL(bt.baggage_type_name,   'No baggage')    AS baggage_type_name,
            fc.class_id
        FROM BookingItem bi
        JOIN FlightPrice fp             ON fp.flight_price_id          = bi.flight_price_id
        JOIN FlightClass fc             ON fc.flight_class_id          = fp.flight_class_id
        LEFT JOIN BaggageOptionInFlight boi
                                        ON boi.booking_item_id         = bi.booking_item_id
        LEFT JOIN BaggagePricingInFlight bpif
                                        ON bpif.baggage_pricing_in_flight_id = boi.baggage_pricing_in_flight_id
        LEFT JOIN BaggagePricingRule bpr
                                        ON bpr.baggage_pricing_rule_id = bpif.baggage_pricing_rule_id
        LEFT JOIN BaggageType bt        ON bt.baggage_type_id          = bpr.baggage_type_id
        WHERE bi.booking_item_id = :booking_item_id
    """), {"booking_item_id": booking_item_id}).mappings().first()

    if not row:
        return None
    return {
        "booking_item_id":   row["booking_item_id"],
        "baggage_quantity":  row["baggage_quantity"],
        "baggage_max_weight": float(row["baggage_max_weight"]),
        "baggage_type_id":   row["baggage_type_id"],
        "baggage_type_name": row["baggage_type_name"],
        "class_id":          row["class_id"],
    }


def get_baggage_types(db: Session) -> list:
    rows = db.execute(text("""
        SELECT baggage_type_id, baggage_type_name
        FROM BaggageType
        WHERE baggage_type_name != 'Carry-on baggage'
        ORDER BY baggage_type_id
    """)).mappings().all()
    return [
        {"baggage_type_id": r["baggage_type_id"], "baggage_type_name": r["baggage_type_name"]}
        for r in rows
    ]


def get_checked_baggage_weight(db: Session, flight_operation_id: int) -> dict:
    weight   = db.execute(text("""
        SELECT dbo.FN_GetCheckedBaggageWeight(:flight_operation_id) AS total_weight
    """), {"flight_operation_id": flight_operation_id}).mappings().first()

    capacity = db.execute(text("""
        SELECT a.baggage_capacity
        FROM FlightOperation fo
        JOIN Airfleet a ON a.airfleet_id = fo.airfleet_id
        WHERE fo.flight_operation_id = :flight_operation_id
    """), {"flight_operation_id": flight_operation_id}).mappings().first()

    return {
        "total_checked_weight_kg": float(weight["total_weight"])       if weight   else 0.0,
        "baggage_capacity_kg":     float(capacity["baggage_capacity"]) if capacity else 0.0,
    }


def get_flight_info_for_booking_item(db: Session, booking_item_id: int) -> dict | None:
    result = db.execute(text("""
        SELECT fc.flight_id, fc.flight_class_id
        FROM BookingItem bi
        JOIN FlightPrice fp ON bi.flight_price_id  = fp.flight_price_id
        JOIN FlightClass fc ON fp.flight_class_id  = fc.flight_class_id
        WHERE bi.booking_item_id = :booking_item_id
    """), {"booking_item_id": booking_item_id}).mappings().first()
    return dict(result) if result else None


def get_booking_baggage_allowance(db: Session, booking_item_id: int) -> dict | None:
    result = db.execute(text("""
        SELECT
            boif.baggage_quantity,
            bpif.baggage_price,
            bpr.baggage_max_weight,
            bt.baggage_type_id,
            bt.baggage_type_name
        FROM BaggageOptionInFlight boif
        JOIN BaggagePricingInFlight bpif
                                ON boif.baggage_pricing_in_flight_id = bpif.baggage_pricing_in_flight_id
        JOIN BaggagePricingRule bpr
                                ON bpif.baggage_pricing_rule_id      = bpr.baggage_pricing_rule_id
        JOIN BaggageType bt     ON bpr.baggage_type_id               = bt.baggage_type_id
        WHERE boif.booking_item_id = :booking_item_id
    """), {"booking_item_id": booking_item_id}).mappings().first()
    return dict(result) if result else None


def get_flight_class_baggage_rules(db: Session, flight_class_id: int) -> list[dict]:
    rows = db.execute(text("""
        SELECT
            bpif.baggage_price,
            bpr.baggage_max_weight,
            bpr.baggage_dimension,
            bt.baggage_type_id,
            bt.baggage_type_name
        FROM BaggagePricingInFlight bpif
        JOIN BaggagePricingRule bpr ON bpif.baggage_pricing_rule_id = bpr.baggage_pricing_rule_id
        JOIN BaggageType bt         ON bpr.baggage_type_id          = bt.baggage_type_id
        WHERE bpif.flight_class_id = :flight_class_id
        ORDER BY bpr.baggage_max_weight ASC
    """), {"flight_class_id": flight_class_id}).mappings().all()
    return [dict(r) for r in rows]


def get_payment_methods(db: Session) -> list:
    rows = db.execute(text("""
        SELECT payment_method_id, payment_method_name
        FROM PaymentMethod
        ORDER BY payment_method_id
    """)).mappings().all()
    return [
        {"payment_method_id": r["payment_method_id"], "payment_method_name": r["payment_method_name"]}
        for r in rows
    ]


def issue_boarding_pass_with_baggage(
    db: Session,
    booking_item_id:     int,
    seat_layout_id:      int,
    flight_operation_id: int,
    checkin_agent_id:    int,
    bags:                list[dict],
    payment_method_id:   int | None,
    total_surcharge:     float,
    status:              str,
) -> dict:
    cafo = db.execute(text("""
        SELECT checkInAgent_flightOperation_id
        FROM CheckInAgentFlightOperation
        WHERE checkin_agent_id = :agent_id
          AND flight_operation_id = :operation_id
    """), {
        "agent_id":     checkin_agent_id,
        "operation_id": flight_operation_id,
    }).mappings().first()

    if not cafo:
        raise ValueError("Agent is not assigned to this flight operation")

    checkin_agent_flight_operation_id = cafo["checkInAgent_flightOperation_id"]

    existing = db.execute(text("""
        SELECT bp.boarding_pass_id, bp.boarding_pass_ticket_number
        FROM BoardingPass bp
        WHERE bp.booking_item_id = :booking_item_id
          AND bp.checkInAgent_flightOperation_id = :cafo_id
    """), {
        "booking_item_id": booking_item_id,
        "cafo_id":         checkin_agent_flight_operation_id,
    }).mappings().first()

    if existing:
        raise ValueError(f"Passenger already checked in. Boarding pass: {existing['boarding_pass_ticket_number']}")

    ticket_number = 'BP' + ''.join(random.choices(string.digits, k=8))

    bp = db.execute(text("""
        INSERT INTO BoardingPass (
            checkInAgent_flightOperation_id,
            seat_layout_id,
            booking_item_id,
            boarding_pass_issue_date_time,
            boarding_pass_ticket_number
        )
        OUTPUT INSERTED.boarding_pass_id, INSERTED.boarding_pass_ticket_number
        VALUES (:cafo_id, :seat_layout_id, :booking_item_id, GETDATE(), :ticket_number)
    """), {
        "cafo_id":         checkin_agent_flight_operation_id,
        "seat_layout_id":  seat_layout_id,
        "booking_item_id": booking_item_id,
        "ticket_number":   ticket_number,
    }).mappings().first()

    boarding_pass_id = bp["boarding_pass_id"]

    carryon = db.execute(text("""
        SELECT baggage_type_id FROM BaggageType
        WHERE baggage_type_name = 'Carry-on baggage'
    """)).mappings().first()
    carryon_type_id = carryon["baggage_type_id"] if carryon else None

    bag_details = []

    if carryon_type_id is not None:
        carryon_tracking = 'TK' + ''.join(random.choices(string.digits, k=10))
        db.execute(text("""
            INSERT INTO BaggageUnit (
                boarding_pass_id, baggage_type_id,
                baggage_unit_tracking_number, baggage_unit_weight_kg
            )
            VALUES (:boarding_pass_id, :baggage_type_id, :tracking, :weight)
        """), {
            "boarding_pass_id": boarding_pass_id,
            "baggage_type_id":  carryon_type_id,
            "tracking":         carryon_tracking,
            "weight":           0,
        })
        bag_details.append({
            "tracking_number":  carryon_tracking,
            "baggage_type_id":  carryon_type_id,
            "baggage_type_name": "Carry-on baggage",
            "weight_kg":        0.0,
        })

    bag_ids = []
    for bag in bags:
        tracking = 'TK' + ''.join(random.choices(string.digits, k=10))
        bu = db.execute(text("""
            INSERT INTO BaggageUnit (
                boarding_pass_id, baggage_type_id,
                baggage_unit_tracking_number, baggage_unit_weight_kg
            )
            OUTPUT INSERTED.baggage_unit_id
            VALUES (:boarding_pass_id, :baggage_type_id, :tracking, :weight)
        """), {
            "boarding_pass_id": boarding_pass_id,
            "baggage_type_id":  bag["baggage_type_id"],
            "tracking":         tracking,
            "weight":           bag["baggage_unit_weight_kg"],
        }).mappings().first()
        bag_ids.append(bu["baggage_unit_id"])

        type_row = db.execute(text("""
            SELECT baggage_type_name FROM BaggageType WHERE baggage_type_id = :type_id
        """), {"type_id": bag["baggage_type_id"]}).mappings().first()

        bag_details.append({
            "tracking_number":   tracking,
            "baggage_type_id":   bag["baggage_type_id"],
            "baggage_type_name": type_row["baggage_type_name"] if type_row else "—",
            "weight_kg":         float(bag["baggage_unit_weight_kg"]),
        })

    checkin_payment_id = None
    if total_surcharge > 0 and payment_method_id:
        pay = db.execute(text("""
            INSERT INTO CheckinInPayment (
                payment_status_id, payment_method_id,
                checkin_payment_date_time, checkin_payment_amount
            )
            OUTPUT INSERTED.checkin_payment_id
            VALUES (
                (SELECT payment_status_id FROM PaymentStatus WHERE payment_status_name = :status),
                :method_id, GETDATE(), :amount
            )
        """), {
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
        "boarding_pass_id":   boarding_pass_id,
        "ticket_number":      ticket_number,
        "checkin_payment_id": checkin_payment_id,
        "bag_count":          len(bag_details),
        "bags":               bag_details,
    }


def get_checkin_agent_by_user_id(db: Session, agent_id: int):
    return db.execute(text("""
        SELECT checkin_agent_id FROM CheckInAgent WHERE checkin_agent_id = :agent_id
    """), {"agent_id": agent_id}).mappings().first()


def check_already_checked_in(
    db: Session,
    booking_item_id:                   int,
    checkin_agent_flight_operation_id: int,
) -> dict | None:
    row = db.execute(text("""
        SELECT bp.boarding_pass_id, bp.boarding_pass_ticket_number
        FROM BoardingPass bp
        WHERE bp.booking_item_id = :booking_item_id
          AND bp.checkInAgent_flightOperation_id = :cafo_id
    """), {
        "booking_item_id": booking_item_id,
        "cafo_id":         checkin_agent_flight_operation_id,
    }).mappings().first()
    return dict(row) if row else None


def get_boarding_stats(db: Session, flight_operation_id: int) -> dict:
    row = db.execute(text("""
        SELECT
            COUNT(DISTINCT bi.booking_item_id)  AS total_passengers,
            COUNT(DISTINCT bp.boarding_pass_id) AS checked_in
        FROM FlightOperation fo
        JOIN ScheduledFlight sf     ON sf.schedule_flight_id  = fo.schedule_flight_id
        JOIN FlightPrice fp         ON fp.schedule_flight_id  = sf.schedule_flight_id
        JOIN FlightClass fc         ON fc.flight_class_id     = fp.flight_class_id
        JOIN BookingItem bi         ON bi.flight_price_id     = fp.flight_price_id
        JOIN Booking b              ON b.booking_id           = bi.booking_id
        JOIN BookingStatus bs       ON bs.booking_status_id   = b.booking_status_id
        LEFT JOIN CheckInAgentFlightOperation cafo
                                    ON cafo.flight_operation_id = fo.flight_operation_id
        LEFT JOIN BoardingPass bp   ON bp.booking_item_id     = bi.booking_item_id
                                    AND bp.checkInAgent_flightOperation_id = cafo.checkInAgent_flightOperation_id
        WHERE fo.flight_operation_id = :flight_operation_id
          AND bs.booking_status_name = 'Confirmed'
    """), {"flight_operation_id": flight_operation_id}).mappings().first()

    total      = row["total_passengers"] if row else 0
    checked_in = row["checked_in"]       if row else 0
    return {
        "total_passengers": total,
        "checked_in":       checked_in,
        "remaining":        total - checked_in,
    }


def get_recently_checked_in(db: Session, flight_operation_id: int) -> list:
    rows = db.execute(text("""
        SELECT
            bp.boarding_pass_id,
            bp.boarding_pass_ticket_number,
            p.passenger_first_name,
            p.passenger_last_name,
            CAST(sl.seat_layout_rows AS VARCHAR) + sl.seat_layout_columns AS seat_position,
            c.class_id,
            c.class_name,
            bp.boarding_pass_issue_date_time,
            cafo.flight_operation_id,
            COUNT(bu.baggage_unit_id) AS bag_count
        FROM BoardingPass bp
        JOIN CheckInAgentFlightOperation cafo
                                ON cafo.checkInAgent_flightOperation_id = bp.checkInAgent_flightOperation_id
        JOIN BookingItem bi      ON bi.booking_item_id     = bp.booking_item_id
        JOIN PassengerDocument pd ON pd.passenger_document_id = bi.passenger_document_id
        JOIN Passenger p         ON p.passenger_id         = pd.passenger_id
        JOIN SeatLayout sl       ON sl.seat_layout_id      = bp.seat_layout_id
        JOIN FlightPrice fp      ON fp.flight_price_id     = bi.flight_price_id
        JOIN FlightClass fc      ON fc.flight_class_id     = fp.flight_class_id
        JOIN Class c             ON c.class_id             = fc.class_id
        LEFT JOIN BaggageUnit bu ON bu.boarding_pass_id    = bp.boarding_pass_id
        WHERE cafo.flight_operation_id = :flight_operation_id
        GROUP BY
            bp.boarding_pass_id, bp.boarding_pass_ticket_number,
            p.passenger_first_name, p.passenger_last_name,
            sl.seat_layout_rows, sl.seat_layout_columns,
            c.class_id, c.class_name,
            bp.boarding_pass_issue_date_time,
            cafo.flight_operation_id
        ORDER BY bp.boarding_pass_issue_date_time DESC
    """), {"flight_operation_id": flight_operation_id}).mappings().all()

    return [
        {
            "boarding_pass_id":    r["boarding_pass_id"],
            "ticket_number":       r["boarding_pass_ticket_number"],
            "passenger_name":      f"{r['passenger_first_name']} {r['passenger_last_name']}",
            "seat":                r["seat_position"],
            "class_id":            r["class_id"],
            "class_name":          r["class_name"],
            "issued_at":           str(r["boarding_pass_issue_date_time"]),
            "flight_operation_id": r["flight_operation_id"],
            "bag_count":           r["bag_count"],
        }
        for r in rows
    ]


def get_boarding_pass_details(db: Session, boarding_pass_id: int) -> dict | None:
    row = db.execute(text("""
        SELECT
            bp.boarding_pass_ticket_number,
            p.passenger_first_name,
            p.passenger_last_name,
            f.flight_number,
            c.class_name,
            CAST(sl.seat_layout_rows AS VARCHAR) + sl.seat_layout_columns AS seat_position,
            sf.departs_date,
            ap_dep.airport_code AS departs_airport,
            ap_arr.airport_code AS arrives_airport,
            g.gate_code,
            COUNT(bu.baggage_unit_id) AS bag_count
        FROM BoardingPass bp
        JOIN CheckInAgentFlightOperation cafo
                                ON cafo.checkInAgent_flightOperation_id = bp.checkInAgent_flightOperation_id
        JOIN FlightOperation fo ON fo.flight_operation_id  = cafo.flight_operation_id
        JOIN ScheduledFlight sf ON sf.schedule_flight_id   = fo.schedule_flight_id
        JOIN Flight f           ON f.flight_id             = sf.flight_id
        JOIN Route r            ON r.route_id              = f.route_id
        JOIN BookingItem bi     ON bi.booking_item_id      = bp.booking_item_id
        JOIN PassengerDocument pd ON pd.passenger_document_id = bi.passenger_document_id
        JOIN Passenger p        ON p.passenger_id          = pd.passenger_id
        JOIN SeatLayout sl      ON sl.seat_layout_id       = bp.seat_layout_id
        JOIN FlightPrice fp     ON fp.flight_price_id      = bi.flight_price_id
        JOIN FlightClass fc     ON fc.flight_class_id      = fp.flight_class_id
        JOIN Class c            ON c.class_id              = fc.class_id
        JOIN Airport ap_dep     ON ap_dep.airport_id       = r.departs_airport_id
        JOIN Airport ap_arr     ON ap_arr.airport_id       = r.arrives_airport_id
        LEFT JOIN Gate g        ON g.gate_id               = fo.gate_id
        LEFT JOIN BaggageUnit bu ON bu.boarding_pass_id    = bp.boarding_pass_id
        WHERE bp.boarding_pass_id = :boarding_pass_id
        GROUP BY
            bp.boarding_pass_ticket_number,
            p.passenger_first_name, p.passenger_last_name,
            f.flight_number, c.class_name,
            sl.seat_layout_rows, sl.seat_layout_columns,
            sf.departs_date,
            ap_dep.airport_code, ap_arr.airport_code,
            g.gate_code
    """), {"boarding_pass_id": boarding_pass_id}).mappings().first()

    if not row:
        return None
    return {
        "ticket_number":   row["boarding_pass_ticket_number"],
        "passenger_name":  f"{row['passenger_first_name']} {row['passenger_last_name']}",
        "flight_number":   row["flight_number"],
        "flight_class":    row["class_name"],
        "seat":            row["seat_position"],
        "departs_date":    str(row["departs_date"]),
        "departs_airport": row["departs_airport"],
        "arrives_airport": row["arrives_airport"],
        "gate":            row["gate_code"],
        "bag_count":       row["bag_count"],
    }


def get_boarding_passes_history(
    db: Session,
    agent_id:    int,
    search:      str | None = None,
    route_city:  str | None = None,
    class_name:  str | None = None,
    date_filter: str | None = "today",
    skip:        int = 0,
    limit:       int = 50,
) -> list:
    date_condition = ""
    if date_filter == "today":
        date_condition = "AND CAST(sf.departs_date AS DATE) = CAST(GETDATE() AS DATE)"
    elif date_filter == "this_week":
        date_condition = (
            "AND sf.departs_date >= DATEADD(DAY, 1 - DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE)) "
            "AND sf.departs_date <  DATEADD(DAY, 8 - DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE))"
        )
    elif date_filter == "this_month":
        date_condition = "AND MONTH(sf.departs_date) = MONTH(GETDATE()) AND YEAR(sf.departs_date) = YEAR(GETDATE())"

    search_condition = ""
    if search:
        search_condition = """
            AND (
                bp.boarding_pass_ticket_number LIKE :search
                OR p.passenger_first_name + ' ' + p.passenger_last_name LIKE :search
                OR f.flight_number LIKE :search
            )
        """

    route_condition = ""
    if route_city:
        route_condition = "AND (dep_city.city_name = :route_city OR arr_city.city_name = :route_city)"

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
            f.flight_number,
            sf.departs_date,
            ap_dep.airport_code     AS departs_airport,
            ap_arr.airport_code     AS arrives_airport,
            dep_city.city_name      AS departs_city,
            arr_city.city_name      AS arrives_city,
            c.class_name,
            CAST(sl.seat_layout_rows AS VARCHAR) + sl.seat_layout_columns AS seat_position,
            COUNT(bu.baggage_unit_id) AS bag_count
        FROM BoardingPass bp
        JOIN CheckInAgentFlightOperation cafo
                                ON cafo.checkInAgent_flightOperation_id = bp.checkInAgent_flightOperation_id
        JOIN CheckInAgent ca    ON ca.checkin_agent_id      = cafo.checkin_agent_id
        JOIN FlightOperation fo ON fo.flight_operation_id   = cafo.flight_operation_id
        JOIN ScheduledFlight sf ON sf.schedule_flight_id    = fo.schedule_flight_id
        JOIN Flight f           ON f.flight_id              = sf.flight_id
        JOIN Route r            ON r.route_id               = f.route_id
        JOIN BookingItem bi     ON bi.booking_item_id       = bp.booking_item_id
        JOIN PassengerDocument pd ON pd.passenger_document_id = bi.passenger_document_id
        JOIN Passenger p        ON p.passenger_id           = pd.passenger_id
        JOIN SeatLayout sl      ON sl.seat_layout_id        = bp.seat_layout_id
        JOIN FlightPrice fp     ON fp.flight_price_id       = bi.flight_price_id
        JOIN FlightClass fc     ON fc.flight_class_id       = fp.flight_class_id
        JOIN Class c            ON c.class_id               = fc.class_id
        JOIN Airport ap_dep     ON ap_dep.airport_id        = r.departs_airport_id
        JOIN Airport ap_arr     ON ap_arr.airport_id        = r.arrives_airport_id
        JOIN City dep_city      ON dep_city.city_id         = ap_dep.city_id
        JOIN City arr_city      ON arr_city.city_id         = ap_arr.city_id
        LEFT JOIN BaggageUnit bu ON bu.boarding_pass_id     = bp.boarding_pass_id
        WHERE ca.checkin_agent_id = :agent_id
        {date_condition}
        {search_condition}
        {route_condition}
        {class_condition}
        GROUP BY
            bp.boarding_pass_id, bp.boarding_pass_ticket_number,
            bp.boarding_pass_issue_date_time,
            p.passenger_first_name, p.passenger_last_name,
            f.flight_number, sf.departs_date,
            ap_dep.airport_code, ap_arr.airport_code,
            dep_city.city_name, arr_city.city_name,
            c.class_name, sl.seat_layout_rows, sl.seat_layout_columns
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
            "boarding_pass_id": r["boarding_pass_id"],
            "ticket_number":    r["boarding_pass_ticket_number"],
            "issued_at":        str(r["boarding_pass_issue_date_time"]),
            "passenger_name":   f"{r['passenger_first_name']} {r['passenger_last_name']}",
            "flight_number":    r["flight_number"],
            "departs_date":     str(r["departs_date"]),
            "departs_airport":  r["departs_airport"],
            "arrives_airport":  r["arrives_airport"],
            "departs_city":     r["departs_city"],
            "arrives_city":     r["arrives_city"],
            "class_name":       r["class_name"],
            "seat":             r["seat_position"],
            "bag_count":        r["bag_count"],
        }
        for r in rows
    ]


def get_baggage_units(db: Session, boarding_pass_id: int) -> list:
    rows = db.execute(text("""
        SELECT
            bu.baggage_unit_id,
            bu.baggage_unit_tracking_number,
            bu.baggage_unit_weight_kg,
            bt.baggage_type_name
        FROM BaggageUnit bu
        JOIN BaggageType bt ON bt.baggage_type_id = bu.baggage_type_id
        WHERE bu.boarding_pass_id = :boarding_pass_id
        ORDER BY bu.baggage_unit_id
    """), {"boarding_pass_id": boarding_pass_id}).mappings().all()
    return [
        {
            "baggage_unit_id":  r["baggage_unit_id"],
            "tracking_number":  r["baggage_unit_tracking_number"],
            "weight_kg":        float(r["baggage_unit_weight_kg"]),
            "baggage_type_name": r["baggage_type_name"],
        }
        for r in rows
    ]


def get_boarding_pass_classes(db: Session, agent_id: int) -> list:
    rows = db.execute(text("""
        SELECT DISTINCT c.class_name
        FROM BoardingPass bp
        JOIN CheckInAgentFlightOperation cafo
                            ON cafo.checkInAgent_flightOperation_id = bp.checkInAgent_flightOperation_id
        JOIN CheckInAgent ca ON ca.checkin_agent_id  = cafo.checkin_agent_id
        JOIN BookingItem bi  ON bi.booking_item_id   = bp.booking_item_id
        JOIN FlightPrice fp  ON fp.flight_price_id   = bi.flight_price_id
        JOIN FlightClass fc  ON fc.flight_class_id   = fp.flight_class_id
        JOIN Class c         ON c.class_id           = fc.class_id
        WHERE ca.checkin_agent_id = :agent_id
        ORDER BY c.class_name
    """), {"agent_id": agent_id}).fetchall()
    return [r[0] for r in rows]


def get_boarding_pass_cities(db: Session, agent_id: int) -> list:
    rows = db.execute(text("""
        SELECT DISTINCT city_name FROM (
            SELECT dep_city.city_name
            FROM BoardingPass bp
            JOIN CheckInAgentFlightOperation cafo
                                ON cafo.checkInAgent_flightOperation_id = bp.checkInAgent_flightOperation_id
            JOIN CheckInAgent ca ON ca.checkin_agent_id   = cafo.checkin_agent_id
            JOIN FlightOperation fo ON fo.flight_operation_id = cafo.flight_operation_id
            JOIN ScheduledFlight sf ON sf.schedule_flight_id  = fo.schedule_flight_id
            JOIN Flight f       ON f.flight_id            = sf.flight_id
            JOIN Route r        ON r.route_id             = f.route_id
            JOIN Airport ap_dep ON ap_dep.airport_id      = r.departs_airport_id
            JOIN City dep_city  ON dep_city.city_id       = ap_dep.city_id
            WHERE ca.checkin_agent_id = :agent_id
            UNION
            SELECT arr_city.city_name
            FROM BoardingPass bp
            JOIN CheckInAgentFlightOperation cafo
                                ON cafo.checkInAgent_flightOperation_id = bp.checkInAgent_flightOperation_id
            JOIN CheckInAgent ca ON ca.checkin_agent_id   = cafo.checkin_agent_id
            JOIN FlightOperation fo ON fo.flight_operation_id = cafo.flight_operation_id
            JOIN ScheduledFlight sf ON sf.schedule_flight_id  = fo.schedule_flight_id
            JOIN Flight f       ON f.flight_id            = sf.flight_id
            JOIN Route r        ON r.route_id             = f.route_id
            JOIN Airport ap_arr ON ap_arr.airport_id      = r.arrives_airport_id
            JOIN City arr_city  ON arr_city.city_id       = ap_arr.city_id
            WHERE ca.checkin_agent_id = :agent_id
        ) cities
        ORDER BY city_name
    """), {"agent_id": agent_id}).fetchall()
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