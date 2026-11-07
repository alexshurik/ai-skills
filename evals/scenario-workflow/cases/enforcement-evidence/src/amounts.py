from decimal import Decimal


def cents(amount: Decimal) -> int:
    return int(amount * 100)
