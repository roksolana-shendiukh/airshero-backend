from sqlalchemy.orm import Session, joinedload

from app.infrastructure.database.models.baggage_model import (
    BaggagePricingInFlight,
    BaggagePricingRule,
    BaggageType,
)


def get_baggage_options(db: Session, flight_class_id: int) -> list:
    rows = (
        db.query(BaggagePricingInFlight)
        .options(
            joinedload(BaggagePricingInFlight.baggage_pricing_rule)
            .joinedload(BaggagePricingRule.baggage_type)
        )
        .filter(BaggagePricingInFlight.flight_class_id == flight_class_id)
        .order_by(BaggagePricingInFlight.baggage_pricing_in_flight_id)
        .all()
    )

    return [
        {
            "baggage_pricing_in_flight_id": r.baggage_pricing_in_flight_id,
            "baggage_pricing_rule_id":      r.baggage_pricing_rule_id,
            "flight_id":                    r.flight_id,
            "flight_class_id":              r.flight_class_id,
            "price":                        float(r.baggage_price),
            "rule": {
                "id":                    r.baggage_pricing_rule.baggage_pricing_rule_id,
                "baggage_type_id":       r.baggage_pricing_rule.baggage_type_id,
                "dimension":             r.baggage_pricing_rule.baggage_dimension,
                "max_weight":            float(r.baggage_pricing_rule.baggage_max_weight),
            },
            "type": {
                "id":   r.baggage_pricing_rule.baggage_type.baggage_type_id,
                "name": r.baggage_pricing_rule.baggage_type.baggage_type_name,
            },
        }
        for r in rows
    ]