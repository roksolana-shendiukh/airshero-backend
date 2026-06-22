from sqlalchemy.orm import Session, joinedload
from app.infrastructure.database.models.baggage_model import BaggagePricingInFlight, BaggagePricingRule, BaggageType


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
            "baggagePricingInFlightId": r.baggage_pricing_in_flight_id,
            "baggagePricingRuleId":     r.baggage_pricing_rule_id,
            "flightId":                 r.flight_id,
            "flightClassId":            r.flight_class_id,
            "price":                    float(r.baggage_price),
            "rule": {
                "id":                 r.baggage_pricing_rule.baggage_pricing_rule_id,
                "baggageTypeId":      r.baggage_pricing_rule.baggage_type_id,
                "dimension":          r.baggage_pricing_rule.baggage_dimension,
                "maxWeight":          float(r.baggage_pricing_rule.baggage_max_weight),
                "overweightFeePerKg": float(r.baggage_pricing_rule.overweight_fee_per_kg),
            },
            "type": {
                "id":   r.baggage_pricing_rule.baggage_type.baggage_type_id,
                "name": r.baggage_pricing_rule.baggage_type.baggage_type_name,
            },
        }
        for r in rows
    ]