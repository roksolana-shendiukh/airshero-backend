OVERWEIGHT_TOLERANCE_KG = 3.0


def _parse_dimensions(dim_str: str) -> tuple[float, float, float]:
    try:
        parts = dim_str.lower().split('x')
        return float(parts[0]), float(parts[1]), float(parts[2])
    except Exception:
        return 0.0, 0.0, 0.0


def _fits_in_dimension(actual_dim: str, limit_dim: str) -> bool:
    al, aw, ah = sorted(_parse_dimensions(actual_dim), reverse=True)
    ll, lw, lh = sorted(_parse_dimensions(limit_dim),  reverse=True)
    return al <= ll and aw <= lw and ah <= lh


def _find_matching_type(
    weight:            float,
    dimension:         str,
    available_pricing: list[dict],
) -> dict | None:
    fitting = [
        p for p in available_pricing
        if _fits_in_dimension(dimension, p['baggage_dimension'])
        and weight <= p['baggage_max_weight'] + OVERWEIGHT_TOLERANCE_KG
    ]

    if fitting:
        return min(fitting, key=lambda p: p['baggage_price'])

    by_size = sorted(
        available_pricing,
        key=lambda p: sum(_parse_dimensions(p['baggage_dimension'])),
        reverse=True,
    )
    return by_size[0] if by_size else None


def calculate_unit_charge(
    unit_weight:       float,
    unit_dimension:    str,
    paid_pricing:      dict,
    available_pricing: list[dict],
    is_extra_unit:     bool,
) -> dict:
    paid_max_weight = paid_pricing['baggage_max_weight']
    paid_fee_per_kg = paid_pricing['overweight_fee_per_kg']
    paid_price      = paid_pricing['baggage_price']
    paid_type_name  = paid_pricing['baggage_type_name']
    paid_dimension  = paid_pricing['baggage_dimension']

    if is_extra_unit:
        matched = _find_matching_type(unit_weight, unit_dimension, available_pricing)
        if matched:
            return {
                'surcharge':              matched['baggage_price'],
                'new_type_name':          matched['baggage_type_name'],
                'reason':                 f"Extra bag — {matched['baggage_type_name']} full payment",
                'requires_full_payment':  True,
            }
        return {
            'surcharge':             paid_price,
            'new_type_name':         None,
            'reason':                'Extra bag — full payment',
            'requires_full_payment': True,
        }

    fits_dim = _fits_in_dimension(unit_dimension, paid_dimension)

    if not fits_dim:
        matched = _find_matching_type(unit_weight, unit_dimension, available_pricing)
        if matched and matched['baggage_type_name'] != paid_type_name:
            diff = matched['baggage_price'] - paid_price
            return {
                'surcharge':             max(round(diff, 2), 0.0),
                'new_type_name':         matched['baggage_type_name'],
                'reason':                f"Size upgrade to {matched['baggage_type_name']}",
                'requires_full_payment': True,
            }

    if unit_weight <= paid_max_weight:
        return {
            'surcharge':             0.0,
            'new_type_name':         None,
            'reason':                'Within allowance',
            'requires_full_payment': False,
        }

    overweight = unit_weight - paid_max_weight

    if overweight <= OVERWEIGHT_TOLERANCE_KG:
        fee = round(overweight * paid_fee_per_kg, 2)
        return {
            'surcharge':             fee,
            'new_type_name':         None,
            'reason':                f"{overweight:.1f}kg overweight × ${paid_fee_per_kg}/kg = ${fee}",
            'requires_full_payment': False,
        }

    matched = _find_matching_type(unit_weight, unit_dimension, available_pricing)

    if matched and matched['baggage_type_name'] != paid_type_name:
        diff = matched['baggage_price'] - paid_price
        return {
            'surcharge':             max(round(diff, 2), 0.0),
            'new_type_name':         matched['baggage_type_name'],
            'reason':                f"Weight exceeds limit, upgraded to {matched['baggage_type_name']}",
            'requires_full_payment': True,
        }

    fee = round(overweight * paid_fee_per_kg, 2)
    return {
        'surcharge':             fee,
        'new_type_name':         None,
        'reason':                f"{overweight:.1f}kg overweight × ${paid_fee_per_kg}/kg = ${fee}",
        'requires_full_payment': False,
    }


def calculate_total_surcharge(
    paid_pricing:      dict,
    actual_units:      list[dict],
    available_pricing: list[dict],
) -> dict:
    """
    actual_units: [{'weight': 25.0, 'dimension': '160x80x70'}, ...]
    """
    paid_qty     = paid_pricing['baggage_quantity']
    total        = 0.0
    unit_results = []

    for i, unit in enumerate(actual_units):
        is_extra = i >= paid_qty
        result   = calculate_unit_charge(
            unit_weight=       unit['weight'],
            unit_dimension=    unit.get('dimension', paid_pricing['baggage_dimension']),
            paid_pricing=      paid_pricing,
            available_pricing= available_pricing,
            is_extra_unit=     is_extra,
        )
        total += result['surcharge']
        unit_results.append({
            'bag_index':             i + 1,
            'surcharge':             result['surcharge'],
            'new_type_name':         result.get('new_type_name'),
            'reason':                result['reason'],
            'requires_full_payment': result['requires_full_payment'],
        })

    return {
        'total_surcharge': round(total, 2),
        'has_surcharge':   total > 0,
        'units':           unit_results,
    }