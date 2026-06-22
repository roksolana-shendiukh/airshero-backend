import math
from collections import deque
from sqlalchemy.orm import Session
from app.infrastructure.database.repositories import route_repository


def get_all_routes(db: Session, airline_id: int | None = None) -> list[dict]:
    routes = route_repository.get_all(db, airline_id=airline_id)
    result = []
    for r in routes:
        dep = r.departs_airport
        arr = r.arrives_airport
        if not dep or not arr:
            continue
        if dep.latitude is None or arr.latitude is None:
            continue
        result.append({
            "routeId":        r.route_id,
            "flightNumber":   r.flight_number,
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


def calculate_haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_all_connecting_flights(
    graph: dict,
    start_city: int,
    end_city: int,
    max_stops: int = 1,
):
    queue = deque([(start_city, [start_city])])
    valid_paths = []
    max_edges = max_stops + 1

    while queue:
        current, path = queue.popleft()

        if current == end_city and len(path) > 1:
            valid_paths.append(path)
            continue

        if len(path) - 1 >= max_edges:
            continue

        for neighbor, weight in graph.get(current, []):
            if neighbor not in path:
                queue.append((neighbor, path + [neighbor]))

    return valid_paths


def get_flight_alternatives(db: Session, from_city: int, to_city: int):
    airports_data = route_repository.get_all_airports_with_cities(db)
    routes_data = route_repository.get_all_route_connections(db)

    graph = {}
    valid_direct_destinations = set()
    for r in routes_data:
        u, v = r["from_id"], r["to_id"]
        w = float(r["flight_range"] or 1.0)
        graph.setdefault(u, []).append((v, w))
        if u == from_city:
            valid_direct_destinations.add(v)

    target_airports = [a for a in airports_data if a["city_id"] == to_city]
    if not target_airports:
        return {"nearbyCities": [], "connectingHubs": []}

    target_lat = float(target_airports[0]["latitude"])
    target_lon = float(target_airports[0]["longitude"])

    nearby_cities = []
    seen_nearby_cities = set()

    for a in airports_data:
        if a["city_id"] in (from_city, to_city):
            continue
        if a["city_id"] in seen_nearby_cities:
            continue
        dist = calculate_haversine_distance(
            target_lat, target_lon,
            float(a["latitude"]), float(a["longitude"]),
        )
        if dist <= 100.0 and a["city_id"] in valid_direct_destinations:
            nearby_cities.append({
                "cityId":     a["city_id"],
                "cityName":   a["city_name"],
                "distanceKm": int(dist),
            })
            seen_nearby_cities.add(a["city_id"])

    connecting_paths = find_all_connecting_flights(
        graph, from_city, to_city, max_stops=1
    )

    connecting_hubs = []
    seen_hubs = set()

    for path in connecting_paths:
        if len(path) != 3:
            continue

        hub_id = path[1]
        if hub_id in seen_hubs:
            continue

        has_valid_pair = route_repository.hub_has_valid_schedule(
            db,
            from_city_id=from_city,
            hub_city_id=hub_id,
            to_city_id=to_city,
        )

        print(f"Hub {hub_id}: has_valid_pair={has_valid_pair}")

        if not has_valid_pair:
            continue

        hub_name = next(
            (a["city_name"] for a in airports_data if a["city_id"] == hub_id),
            "Connecting Hub",
        )
        connecting_hubs.append({
            "cityId":   hub_id,
            "cityName": hub_name,
        })
        seen_hubs.add(hub_id)

    return {
        "nearbyCities":   nearby_cities,
        "connectingHubs": connecting_hubs,
    }


    

