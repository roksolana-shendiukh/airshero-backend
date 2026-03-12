from sqlalchemy.orm import Session
from app.models.route_model import Route
from app.repositories import route_repository


def get_all_routes(db: Session) -> list[dict]:
    routes = route_repository.get_all(db)
    result = []
    for r in routes:
        dep = r.departs_airport
        arr = r.arrives_airport
        if not dep or not arr:
            continue
        if dep.latitude is None or arr.latitude is None:
            continue
        result.append({
            "routeId":         r.route_id,
            "flightNumber":    r.flight_number,
            "departsAirport": {
                "airportId":   dep.airport_id,
                "airportCode": dep.airport_code,
                "latitude":    float(dep.latitude),
                "longitude":   float(dep.longitude),
            },
            "arrivesAirport": {
                "airportId":   arr.airport_id,
                "airportCode": arr.airport_code,
                "latitude":    float(arr.latitude),
                "longitude":   float(arr.longitude),
            },
        })
    return result