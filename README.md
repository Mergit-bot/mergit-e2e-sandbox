# Northwind Fulfilment

The warehouse service behind the Northwind storefront: it prices baskets, holds stock
while a customer is paying, moves orders through their lifecycle, imports the nightly
supplier feed and produces the numbers on the ops dashboard.

Standard library only. No database, no framework — everything is an in-memory structure,
so the whole service can be exercised from a REPL or a test without infrastructure.

## Layout

| Module | What it owns |
| --- | --- |
| `fulfilment/catalog.py` | Products, SKUs, and the quantity-discount tiers attached to them |
| `fulfilment/pricing.py` | What a basket costs: tiers, promotions, shipping, tax |
| `fulfilment/inventory.py` | On hand, reserved, damaged — and what can still be sold |
| `fulfilment/orders.py` | The order state machine and the money attached to it |
| `fulfilment/reporting.py` | Daily rollups, percentiles and rankings for the dashboard |
| `fulfilment/supplier_feed.py` | The nightly supplier CSV drop |

## Running it

```bash
python -m pytest -q
```

A quick look at the pricing path:

```python
from fulfilment.catalog import demo_catalog
from fulfilment.pricing import BasketLine, quote_basket, format_money

catalog = demo_catalog()
quote = quote_basket(catalog, [BasketLine(sku="WID-100", quantity=12)])
print(format_money(quote.total_cents))
```

## Conventions

**Money is in whole cents, everywhere.** It is converted to a decimal string exactly
once, at the edge, by `pricing.format_money`. A float that holds an amount of money is a
bug waiting for a rounding complaint.

**Stock is three numbers, not one.** `on_hand` is what is physically in the building,
`reserved` is what is promised to a basket that has not paid yet, and `damaged` is
present-but-unsellable. What a new customer can buy is `on_hand - reserved`, and code
that reaches for `on_hand` alone will oversell.

**Transitions are recorded, not inferred.** Every order carries its own history, so
support answers "what happened to this order" from the record rather than from a log
file.

**An import that skips a row must say so.** A supplier line that vanishes quietly is
stock the warehouse believes it has and does not.

## Contributing

One logical change per pull request. Every bug fix comes with the regression test that
fails without it. The test suite is expected to be green on `main` at all times — CI runs
it on every pull request.
