from decimal import Decimal, ROUND_HALF_UP


def normalize_percent(value) -> Decimal:
    """
    Accepts:
      - '0.044'
      - '4.4%'
      - 0.044
      - 4.4
    Returns:
      Decimal('4.40')
    """
    if value is None:
        return None

    value = str(value).strip()

    if value.endswith('%'):
        return Decimal(value.replace('%', '')).quantize(Decimal('0.01'))

    d = Decimal(value)

    # if <= 1 assume fraction (0.044 → 4.4)
    if d <= 1:
        d = d * 100

    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

