from sqlalchemy.orm import Session
from sqlalchemy import text

_SEARCH_CITIES = text("""
    SELECT DISTINCT TOP 10
        ci.city_id,
        ci.city_name,
        co.country_name,
        CASE
            WHEN ci.city_name LIKE :q_start THEN 0
            WHEN co.country_name LIKE :q_start THEN 1
            ELSE 2
        END AS sort_order
    FROM City ci
    JOIN Country co ON ci.country_id = co.country_id
    WHERE
        ci.city_name LIKE :q
        OR co.country_name LIKE :q
    ORDER BY sort_order, ci.city_name
""")

_GET_ALTERNATIVES = """
    SELECT DISTINCT 
        dest_city.city_id, 
        dest_city.city_name, 
        co.country_name
    FROM Flight f
    JOIN FlightSchedule fs ON f.flight_schedule_id = fs.flight_schedule_id
    JOIN Route r ON fs.route_id = r.route_id
    JOIN Airport arr_airport ON r.arrives_airport_id = arr_airport.airport_id
    JOIN City dest_city ON arr_airport.city_id = dest_city.city_id
    JOIN Country co ON dest_city.country_id = co.country_id
    JOIN Airport dep_airport ON r.departs_airport_id = dep_airport.airport_id
    WHERE dep_airport.city_id = :from_id
"""

_GET_AVAILABLE_DATES = """
    SELECT DISTINCT CAST(f.departs_datetime AS DATE) as available_date
    FROM Flight f
    JOIN FlightSchedule fs ON f.flight_schedule_id = fs.flight_schedule_id
    JOIN Route r ON fs.route_id = r.route_id
    JOIN Airport dep_airport ON r.departs_airport_id = dep_airport.airport_id
    JOIN Airport arr_airport ON r.arrives_airport_id = arr_airport.airport_id
    WHERE dep_airport.city_id = :from_id 
      AND arr_airport.city_id = :to_id
    -- Тимчасово прибираємо фільтр дати для тесту
    -- AND f.departs_datetime >= GETDATE() 
    ORDER BY available_date
"""
def get_alternatives(db: Session, from_city_id: int):
    return db.execute(text(_GET_ALTERNATIVES), {"from_id": from_city_id}).fetchall()

def search_cities(db: Session, query: str):
    return db.execute(_SEARCH_CITIES, {
        "q": f"%{query}%",
        "q_start": f"{query}%",
    }).fetchall()

def get_available_dates(db: Session, from_city_id: int, to_city_id: int):
    rows = db.execute(text(_GET_AVAILABLE_DATES), {
        "from_id": from_city_id,
        "to_id": to_city_id
    }).fetchall()
    
    return [str(row.available_date) for row in rows]