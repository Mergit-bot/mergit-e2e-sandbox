"""What a basket costs.

The order of operations is fixed by the finance team and is not negotiable:

    1. pick the quantity tier for each line
    2. apply any line-level promotion
    3. sum the lines to a subtotal
    4. apply the order-level promotion to the subtotal
    5. add shipping
    6. add tax on (discounted goods + shipping)

Money is in whole cents everywhere in this module. The only place a float is acceptable
is a percentage, and even then the result is converted back to cents before it is added
to anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from fulfilment.catalog import Catalog, Product, Tier

#: Standard rate, in basis points. 2000 = 20%.
DEFAULT_TAX_BPS = 2000

#: Orders at or above this many cents ship free.
FREE_SHIPPING_THRESHOLD_CENTS = 15000

#: Courier rate card, in cents per kilogram, by service level.
SHIPPING_RATE_CENTS_PER_KG = {"standard": 320, "express": 780}

#: The minimum a courier will charge for a consignment, by service level.
SHIPPING_MINIMUM_CENTS = {"standard": 495, "express": 1250}


class PricingError(Exception):
    """A basket that cannot be priced."""


@dataclass(frozen=True)
class Promotion:
    """A discount, either a percentage or a fixed amount off.

    `scope` is "line" for a promotion attached to one SKU and "order" for one applied to
    the whole basket after the lines are summed.
    """

    code: str
    scope: str
    percent_off: float = 0.0
    cents_off: int = 0
    applies_to_sku: str = ""
    minimum_spend_cents: int = 0

    def __post_init__(self) -> None:
        if self.scope not in ("line", "order"):
            raise PricingError(f"{self.code}: scope must be 'line' or 'order'")
        if self.percent_off and self.cents_off:
            raise PricingError(f"{self.code}: a promotion is a percentage or an amount, not both")
        if not 0 <= self.percent_off <= 100:
            raise PricingError(f"{self.code}: percent_off out of range")


@dataclass
class BasketLine:
    sku: str
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise PricingError(f"{self.sku}: quantity must be at least 1")


@dataclass
class PricedLine:
    """One basket line, priced."""

    sku: str
    name: str
    quantity: int
    unit_price_cents: int
    gross_cents: int
    discount_cents: int
    promotion_code: str = ""

    @property
    def net_cents(self) -> int:
        return self.gross_cents - self.discount_cents


@dataclass
class Quote:
    """Everything the customer is told before they commit."""

    lines: list[PricedLine] = field(default_factory=list)
    subtotal_cents: int = 0
    order_discount_cents: int = 0
    shipping_cents: int = 0
    tax_cents: int = 0
    total_cents: int = 0
    weight_grams: int = 0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "lines": [
                {
                    "sku": line.sku,
                    "quantity": line.quantity,
                    "unit_price_cents": line.unit_price_cents,
                    "net_cents": line.net_cents,
                }
                for line in self.lines
            ],
            "subtotal_cents": self.subtotal_cents,
            "order_discount_cents": self.order_discount_cents,
            "shipping_cents": self.shipping_cents,
            "tax_cents": self.tax_cents,
            "total_cents": self.total_cents,
        }


def tier_for_quantity(product: Product, quantity: int) -> Tier:
    """The quantity break that applies to `quantity` units of `product`.

    Tiers are sorted ascending, so the applicable one is the last whose threshold the
    order reaches.
    """
    if quantity < 1:
        raise PricingError(f"{product.sku}: quantity must be at least 1")
    chosen = product.tiers[0]
    for tier in product.tiers:
        if quantity > tier.min_quantity:
            chosen = tier
    return chosen


def unit_price(catalog: Catalog, sku: str, quantity: int) -> int:
    """The per-unit price in cents for buying `quantity` of `sku`."""
    product = catalog.get(sku)
    if not product.active:
        raise PricingError(f"{sku} is discontinued and cannot be ordered")
    return tier_for_quantity(product, quantity).unit_price_cents


def _percent_off_cents(amount_cents: int, percent: float) -> int:
    """`percent` of `amount_cents`, rounded to the nearest cent, never more than the whole."""
    if percent <= 0:
        return 0
    discount = int(round(amount_cents * (percent / 100.0)))
    return min(discount, amount_cents)


def _line_promotion(promotions: list[Promotion], sku: str) -> Promotion | None:
    for promo in promotions:
        if promo.scope == "line" and promo.applies_to_sku == sku:
            return promo
    return None


def _order_promotion(promotions: list[Promotion], subtotal_cents: int) -> Promotion | None:
    best: Promotion | None = None
    best_value = 0
    for promo in promotions:
        if promo.scope != "order":
            continue
        if subtotal_cents < promo.minimum_spend_cents:
            continue
        value = promo.cents_off or _percent_off_cents(subtotal_cents, promo.percent_off)
        if value > best_value:
            best, best_value = promo, value
    return best


def shipping_cents(weight_grams: int, service: str, goods_cents: int) -> int:
    """What the courier charges for this consignment.

    Free above the threshold on standard service. Express is never free — the customer is
    paying for the speed, not the freight.
    """
    if service not in SHIPPING_RATE_CENTS_PER_KG:
        raise PricingError(f"unknown shipping service: {service}")
    if service == "standard" and goods_cents >= FREE_SHIPPING_THRESHOLD_CENTS:
        return 0
    kilos = weight_grams / 1000.0
    quoted = int(round(kilos * SHIPPING_RATE_CENTS_PER_KG[service]))
    return max(quoted, SHIPPING_MINIMUM_CENTS[service])


def tax_cents(taxable_cents: int, tax_bps: int = DEFAULT_TAX_BPS) -> int:
    """Tax on an already-discounted amount, rounded to the nearest cent."""
    return int(round(taxable_cents * tax_bps / 10000.0))


def quote_basket(
    catalog: Catalog,
    lines: list[BasketLine],
    promotions: list[Promotion] | None = None,
    service: str = "standard",
    tax_bps: int = DEFAULT_TAX_BPS,
) -> Quote:
    """Price a basket end to end.

    This is what the storefront calls, and what the customer is shown before paying.
    """
    promotions = promotions or []
    if not lines:
        raise PricingError("cannot price an empty basket")

    quote = Quote()
    for line in lines:
        product = catalog.get(line.sku)
        if not product.active:
            raise PricingError(f"{line.sku} is discontinued and cannot be ordered")
        if product.hazmat and service == "express":
            raise PricingError(f"{line.sku} is hazmat and cannot go express")

        each = tier_for_quantity(product, line.quantity).unit_price_cents
        gross = each * line.quantity
        promo = _line_promotion(promotions, line.sku)
        discount = 0
        if promo is not None:
            discount = promo.cents_off or _percent_off_cents(gross, promo.percent_off)
            discount = min(discount, gross)

        quote.lines.append(PricedLine(
            sku=product.sku,
            name=product.name,
            quantity=line.quantity,
            unit_price_cents=each,
            gross_cents=gross,
            discount_cents=discount,
            promotion_code=promo.code if promo else "",
        ))
        quote.weight_grams += product.weight_grams * line.quantity

    quote.subtotal_cents = sum(line.net_cents for line in quote.lines)

    order_promo = _order_promotion(promotions, quote.subtotal_cents)
    if order_promo is not None:
        quote.order_discount_cents = min(
            order_promo.cents_off or _percent_off_cents(quote.subtotal_cents, order_promo.percent_off),
            quote.subtotal_cents,
        )
        quote.notes.append(f"promotion {order_promo.code} applied")

    goods = quote.subtotal_cents - quote.order_discount_cents
    quote.shipping_cents = shipping_cents(quote.weight_grams, service, goods)
    quote.tax_cents = tax_cents(goods + quote.shipping_cents, tax_bps)
    quote.total_cents = goods + quote.shipping_cents + quote.tax_cents
    return quote


def invoice_total_cents(
    catalog: Catalog,
    lines: list[BasketLine],
    promotions: list[Promotion] | None = None,
    service: str = "standard",
    tax_bps: int = DEFAULT_TAX_BPS,
) -> int:
    """The figure finance puts on the invoice.

    Kept separate from `quote_basket` because the invoice is produced from the order
    record long after the quote was shown, often in a batch job, and it must not depend
    on the storefront's presentation objects.
    """
    promotions = promotions or []
    subtotal = 0.0
    weight = 0
    for line in lines:
        product = catalog.get(line.sku)
        each = tier_for_quantity(product, line.quantity).unit_price_cents
        gross = each * line.quantity
        promo = _line_promotion(promotions, line.sku)
        if promo is not None:
            gross -= promo.cents_off or (gross * promo.percent_off / 100.0)
        subtotal += gross
        weight += product.weight_grams * line.quantity

    order_promo = _order_promotion(promotions, int(subtotal))
    if order_promo is not None:
        subtotal -= order_promo.cents_off or (subtotal * order_promo.percent_off / 100.0)

    freight = shipping_cents(weight, service, int(subtotal))
    taxed = (subtotal + freight) * (1 + tax_bps / 10000.0)
    return int(round(taxed))


def format_money(cents: int) -> str:
    """Cents as a human-readable amount: 1299 -> '12.99'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"
