"""The nightly supplier CSV."""
from fulfilment.inventory import Warehouse
from fulfilment.supplier_feed import (
    apply_to_warehouse,
    is_header,
    parse_feed,
    reconcile,
)

PLAIN_FEED = """sku,description,quantity,unit_cost_cents,expected_date
WID-100,Widget standard,120,850,2026-09-20
GRM-010,Brass grommet,900,180,2026-09-21
ANV-001,Anvil 50kg,4,14000,2026-09-25
"""


def test_the_header_is_recognised():
    assert is_header(["sku", "description", "quantity", "unit_cost_cents", "expected_date"])
    assert not is_header(["WID-100", "Widget", "1", "1", "2026-01-01"])


def test_a_plain_feed_imports_every_row():
    result = parse_feed(PLAIN_FEED, supplier="acme")
    assert result.imported == 3
    assert result.total_units == 120 + 900 + 4
    assert result.ok is True


def test_blank_lines_are_ignored():
    result = parse_feed(PLAIN_FEED + "\n\n\n", supplier="acme")
    assert result.imported == 3


def test_skus_are_upper_cased():
    result = parse_feed("wid-100,Widget,5,100,2026-09-20", supplier="acme")
    assert result.rows[0].sku == "WID-100"


def test_extended_cost_multiplies_out():
    result = parse_feed("WID-100,Widget,10,850,2026-09-20", supplier="acme")
    assert result.rows[0].extended_cost_cents == 8500


def test_a_negative_quantity_is_not_imported():
    result = parse_feed("WID-100,Widget,-5,850,2026-09-20", supplier="acme")
    assert result.imported == 0


def test_an_import_books_stock_in():
    warehouse = Warehouse()
    result = parse_feed(PLAIN_FEED, supplier="acme")
    touched = apply_to_warehouse(result, warehouse)
    assert sorted(touched) == ["ANV-001", "GRM-010", "WID-100"]
    assert warehouse.stock("WID-100").on_hand == 120


def test_reconcile_reports_only_the_differences():
    result = parse_feed(PLAIN_FEED, supplier="acme")
    difference = reconcile(result, {"WID-100": 120, "GRM-010": 1000, "ANV-001": 4})
    assert difference == {"GRM-010": -100}


def test_the_summary_names_the_supplier():
    result = parse_feed(PLAIN_FEED, supplier="acme")
    assert result.summary().startswith("acme: imported 3 rows")
