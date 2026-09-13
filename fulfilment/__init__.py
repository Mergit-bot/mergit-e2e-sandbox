"""Northwind Fulfilment — order pricing, stock and reporting for the warehouse service.

The package is deliberately plain: standard library only, no framework, no database.
Everything is an in-memory structure so the service can be exercised from a REPL or a
test without infrastructure.

Modules
-------
catalog        products, SKUs and the quantity-discount tiers attached to them
pricing        what a basket costs: tiers, promotions, tax and rounding
inventory      what is on hand, what is promised to someone else, what can be sold
orders         the order lifecycle and the money attached to it
reporting      daily rollups, percentiles and rankings for the ops dashboard
supplier_feed  the nightly CSV drop from suppliers
"""

__version__ = "2.4.0"
