from sqlalchemy.orm import Session
from app.repositories.queries.baggage_queries import GET_BAGGAGE_OPTIONS_FOR_FLIGHT


def get_baggage_options(db: Session, flight_class_id: int) -> list:
    rows = db.execute(GET_BAGGAGE_OPTIONS_FOR_FLIGHT, {
        "flight_class_id": flight_class_id,
    }).fetchall()

    return [
        {
            "baggagePricingInFlightId": row.baggage_pricing_in_flight_id,
            "baggagePricingRuleId":     row.baggage_pricing_rule_id,
            "flightId":                 row.flight_id,
            "flightClassId":            row.flight_class_id,
            "price":                    float(row.baggage_price),
            "rule": {
                "id":                  row.baggage_pricing_rule_id,
                "baggageTypeId":       row.baggage_type_id,
                "dimension":           row.baggage_dimension,
                "maxWeight":           float(row.baggage_max_weight),
                "overweightFeePerKg":  float(row.overweight_fee_per_kg),
            },
            "type": {
                "id":   row.baggage_type_id,
                "name": row.baggage_type_name,
            },
        }
        for row in rows
    ]