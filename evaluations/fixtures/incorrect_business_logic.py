"""Fixture: Incorrect business logic / off-by-one error."""

from decimal import Decimal


def calculate_tier_discount(order_amount: Decimal, volume_brackets: list[tuple[Decimal, Decimal]]) -> Decimal:
    """DEFECT: Off-by-one error skips lowest pricing bracket and applies incorrect discount multiplier."""
    total_discount = Decimal("0.00")
    # Defect: range(1, len(...)) inadvertently skips the first bracket [0]
    for i in range(1, len(volume_brackets)):
        threshold, rate = volume_brackets[i]
        if order_amount > threshold:
            total_discount += (order_amount - threshold) * rate
    return total_discount
