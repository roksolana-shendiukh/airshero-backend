from sqlalchemy import text

GET_BAGGAGE_OPTIONS_FOR_FLIGHT = text("""
    SELECT
        bpf.baggage_pricing_in_flight_id,
        bpf.baggage_pricing_rule_id,
        bpf.flight_id,
        bpf.flight_class_id,
        bpf.baggage_price,
        bpr.baggage_type_id,
        bpr.baggage_dimension,
        bpr.baggage_max_weight,
        bpr.overweight_fee_per_kg,
        bt.baggage_type_name
    FROM BaggagePricingInFlight bpf
    JOIN BaggagePricingRule bpr
        ON bpf.baggage_pricing_rule_id = bpr.baggage_pricing_rule_id
    JOIN BaggageType bt
        ON bpr.baggage_type_id = bt.baggage_type_id
    WHERE bpf.flight_class_id = :flight_class_id
    ORDER BY bpf.baggage_pricing_in_flight_id
""")