"""Pricing: tiers, promotions, shipping and tax."""
import pytest

from fulfilment.catalog import demo_catalog
from fulfilment.pricing import (
    BasketLine,
    Promotion,
    PricingError,
    format_money,
    quote_basket,
    shipping_cents,
    tax_cents,
    unit_price,
)


@pytest.fixture()
def catalog():
    return demo_catalog()


def test_a_single_unit_is_charged_the_list_price(catalog):
    assert unit_price(catalog, "WID-100", 1) == 1299


def test_a_quantity_inside_a_tier_gets_that_tiers_price(catalog):
    assert unit_price(catalog, "WID-100", 12) == 1199
    assert unit_price(catalog, "WID-100", 60) == 999
    assert unit_price(catalog, "WID-100", 300) == 899


def test_a_product_without_tiers_always_costs_list_price(catalog):
    assert unit_price(catalog, "ANV-001", 1) == 18900
    assert unit_price(catalog, "ANV-001", 40) == 18900


def test_a_discontinued_product_cannot_be_priced(catalog):
    with pytest.raises(PricingError):
        unit_price(catalog, "WID-050", 1)


def test_an_empty_basket_is_refused(catalog):
    with pytest.raises(PricingError):
        quote_basket(catalog, [])


def test_a_basket_totals_its_lines(catalog):
    quote = quote_basket(catalog, [
        BasketLine(sku="WID-100", quantity=2),
        BasketLine(sku="GRM-010", quantity=3),
    ])
    assert quote.subtotal_cents == 2 * 1299 + 3 * 349
    assert quote.total_cents == quote.subtotal_cents + quote.shipping_cents + quote.tax_cents


def test_a_line_promotion_only_touches_its_own_sku(catalog):
    promo = Promotion(code="GRM20", scope="line", percent_off=20.0, applies_to_sku="GRM-010")
    quote = quote_basket(catalog, [
        BasketLine(sku="WID-100", quantity=2),
        BasketLine(sku="GRM-010", quantity=4),
    ], promotions=[promo])

    widgets = next(line for line in quote.lines if line.sku == "WID-100")
    grommets = next(line for line in quote.lines if line.sku == "GRM-010")
    assert widgets.discount_cents == 0
    assert grommets.discount_cents == int(round(4 * 349 * 0.2))


def test_an_order_promotion_needs_the_minimum_spend(catalog):
    promo = Promotion(code="SAVE10", scope="order", cents_off=1000,
                      minimum_spend_cents=100_000)
    quote = quote_basket(catalog, [BasketLine(sku="WID-100", quantity=2)],
                         promotions=[promo])
    assert quote.order_discount_cents == 0


def test_a_promotion_cannot_discount_more_than_the_line(catalog):
    promo = Promotion(code="HUGE", scope="line", cents_off=999_999,
                      applies_to_sku="GRM-010")
    quote = quote_basket(catalog, [BasketLine(sku="GRM-010", quantity=1)],
                         promotions=[promo])
    assert quote.lines[0].net_cents == 0


def test_shipping_is_free_on_standard_above_the_threshold():
    assert shipping_cents(weight_grams=4000, service="standard", goods_cents=20_000) == 0


def test_express_is_never_free():
    assert shipping_cents(weight_grams=4000, service="express", goods_cents=20_000) > 0


def test_a_light_parcel_pays_the_courier_minimum():
    assert shipping_cents(weight_grams=30, service="standard", goods_cents=500) == 495


def test_hazmat_cannot_go_express(catalog):
    with pytest.raises(PricingError):
        quote_basket(catalog, [BasketLine(sku="SOL-050", quantity=1)], service="express")


def test_tax_is_twenty_percent_by_default():
    assert tax_cents(10_000) == 2000


def test_money_formats_with_two_decimal_places():
    assert format_money(1299) == "12.99"
    assert format_money(5) == "0.05"
    assert format_money(-250) == "-2.50"
