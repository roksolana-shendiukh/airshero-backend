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
        if _fits_in_dimension(dimension, p['baggageDimension'])
        and weight <= p['baggageMaxWeight'] + OVERWEIGHT_TOLERANCE_KG
    ]

    if fitting:
        return min(fitting, key=lambda p: p['baggagePrice'])

    by_size = sorted(
        available_pricing,
        key=lambda p: sum(_parse_dimensions(p['baggageDimension'])),
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
    paid_max_weight   = paid_pricing['baggageMaxWeight']
    paid_fee_per_kg   = paid_pricing['overweightFeePerKg']
    paid_price        = paid_pricing['baggagePrice']
    paid_type_name    = paid_pricing['baggageTypeName']
    paid_dimension    = paid_pricing['baggageDimension']

    if is_extra_unit:
        matched = _find_matching_type(
            unit_weight, unit_dimension, available_pricing
        )
        if matched:
            return {
                'surcharge':            matched['baggagePrice'],
                'newTypeName':          matched['baggageTypeName'],
                'reason':               f"Extra bag — {matched['baggageTypeName']} full payment",
                'requiresFullPayment':  True,
            }
        return {
            'surcharge':            paid_price,
            'newTypeName':          None,
            'reason':               'Extra bag — full payment',
            'requiresFullPayment':  True,
        }

    fits_dim = _fits_in_dimension(unit_dimension, paid_dimension)

    if not fits_dim:
        matched = _find_matching_type(
            unit_weight, unit_dimension, available_pricing
        )
        if matched and matched['baggageTypeName'] != paid_type_name:
            diff = matched['baggagePrice'] - paid_price
            return {
                'surcharge':            max(round(diff, 2), 0.0),
                'newTypeName':          matched['baggageTypeName'],
                'reason':               f"Size upgrade to {matched['baggageTypeName']}",
                'requiresFullPayment':  True,
            }

    if unit_weight <= paid_max_weight:
        return {
            'surcharge':            0.0,
            'newTypeName':          None,
            'reason':               'Within allowance',
            'requiresFullPayment':  False,
        }

    overweight = unit_weight - paid_max_weight

    if overweight <= OVERWEIGHT_TOLERANCE_KG:
        fee = round(overweight * paid_fee_per_kg, 2)
        return {
            'surcharge':            fee,
            'newTypeName':          None,
            'reason':               f"{overweight:.1f}kg overweight × ${paid_fee_per_kg}/kg = ${fee}",
            'requiresFullPayment':  False,
        }

    matched = _find_matching_type(
        unit_weight, unit_dimension, available_pricing
    )

    if matched and matched['baggageTypeName'] != paid_type_name:
        diff = matched['baggagePrice'] - paid_price
        return {
            'surcharge':            max(round(diff, 2), 0.0),
            'newTypeName':          matched['baggageTypeName'],
            'reason':               f"Weight exceeds limit, upgraded to {matched['baggageTypeName']}",
            'requiresFullPayment':  True,
        }

    fee = round(overweight * paid_fee_per_kg, 2)
    return {
        'surcharge':            fee,
        'newTypeName':          None,
        'reason':               f"{overweight:.1f}kg overweight × ${paid_fee_per_kg}/kg = ${fee}",
        'requiresFullPayment':  False,
    }


def calculate_total_surcharge(
    paid_pricing:      dict,
    actual_units:      list[dict],
    available_pricing: list[dict],
) -> dict:
    """
    actual_units: [{'weight': 25.0, 'dimension': '160x80x70'}, ...]
    """
    paid_qty     = paid_pricing['baggageQuantity']
    total        = 0.0
    unit_results = []

    for i, unit in enumerate(actual_units):
        is_extra = i >= paid_qty
        result   = calculate_unit_charge(
            unit_weight       = unit['weight'],
            unit_dimension    = unit.get('dimension', paid_pricing['baggageDimension']),
            paid_pricing      = paid_pricing,
            available_pricing = available_pricing,
            is_extra_unit     = is_extra,
        )
        total += result['surcharge']
        unit_results.append({
            'bagIndex':           i + 1,
            'surcharge':          result['surcharge'],
            'newTypeName':        result.get('newTypeName'),
            'reason':             result['reason'],
            'requiresFullPayment': result['requiresFullPayment'],
        })

    return {
        'totalSurcharge': round(total, 2),
        'hasSurcharge':   total > 0,
        'units':          unit_results,
    }