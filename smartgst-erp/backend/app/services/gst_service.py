from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


MONEY = Decimal("0.01")


@dataclass(frozen=True)
class TaxBreakdown:
    subtotal: Decimal
    cgst: Decimal
    sgst: Decimal
    igst: Decimal
    total: Decimal


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_tax(
    subtotal: Decimal,
    gst_rate: float,
    seller_state: str | None = None,
    place_of_supply: str | None = None,
) -> TaxBreakdown:
    """Calculate GST while retaining the old intra-state default behavior."""
    subtotal = money(Decimal(subtotal))
    tax = money(subtotal * Decimal(str(gst_rate)) / Decimal("100"))
    interstate = bool(seller_state and place_of_supply and seller_state.strip().lower() != place_of_supply.strip().lower())
    if interstate:
        return TaxBreakdown(subtotal, Decimal("0.00"), Decimal("0.00"), tax, money(subtotal + tax))
    half_tax = money(tax / Decimal("2"))
    return TaxBreakdown(subtotal, half_tax, money(tax - half_tax), Decimal("0.00"), money(subtotal + tax))
