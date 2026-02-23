from sqlalchemy.orm import Session
from sqlalchemy import text

_SEARCH_FLIGHTS = text("""
    SELECT 
        f.flight_id,
        r.flight_number,
        f.departs_datetime,
        f.arrives_datetime,
        al.airline_name,
        '' as airline_logo_url,
        dep_ap.airport_code as departs_code,
        dep_ap.airport_name as departs_airport, 
        arr_ap.airport_code as arrives_code,
        arr_ap.airport_name as arrives_airport, 
        c.class_name,
        fp.ticket_price
    FROM Flight f
    JOIN FlightSchedule fs ON f.flight_schedule_id = fs.flight_schedule_id
    JOIN Route r ON fs.route_id = r.route_id
    JOIN Airline al ON r.airline_id = al.airline_id
    JOIN Airport dep_ap ON r.departs_airport_id = dep_ap.airport_id
    JOIN Airport arr_ap ON r.arrives_airport_id = arr_ap.airport_id
    JOIN FlightClass fc ON f.flight_id = fc.flight_id
    JOIN FlightPrice fp ON fc.flight_class_id = fp.flight_class_id
    JOIN Class c ON fc.class_id = c.class_id
    WHERE dep_ap.city_id = :from_id 
      AND arr_ap.city_id = :to_id
      AND CAST(f.departs_datetime AS DATE) = CAST(:depart_date AS DATE)
""")

def search_flights(db: Session, from_city: int, to_city: int, depart_date: str):
    result = db.execute(_SEARCH_FLIGHTS, {
        "from_id": from_city,
        "to_id": to_city,
        "depart_date": depart_date
    })
    return result.all()

