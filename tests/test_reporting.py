"""Dashboard numbers."""
import pytest

from fulfilment.orders import OrderBook, OrderLine
from fulfilment.reporting import (
    ReportError,
    daily_rollups,
    fulfilment_rate,
    percentile,
    summary_stats,
    top_products,
)


@pytest.fixture()
def book():
    book = OrderBook()
    for customer, sku, qty in [("cus_1", "WID-100", 3), ("cus_2", "GRM-010", 10),
                               ("cus_3", "WID-100", 5)]:
        book.create(customer, [OrderLine(sku=sku, quantity=qty, unit_price_cents=1000)],
                    total_cents=qty * 1000)
    return book


def test_the_median_of_an_odd_number_of_samples(book):
    assert percentile([1.0, 2.0, 3.0], 50) == 2.0


def test_a_percentile_of_nothing_is_an_error():
    with pytest.raises(ReportError):
        percentile([], 50)


def test_a_percentile_outside_the_range_is_an_error():
    with pytest.raises(ReportError):
        percentile([1.0], 101)


def test_summary_stats_of_an_empty_series_are_zero():
    stats = summary_stats([])
    assert stats["count"] == 0
    assert stats["mean"] == 0.0


def test_summary_stats_report_the_obvious_numbers():
    stats = summary_stats([2.0, 4.0, 6.0, 8.0])
    assert stats["count"] == 4
    assert stats["min"] == 2.0
    assert stats["max"] == 8.0
    assert stats["mean"] == 5.0


def test_top_products_never_returns_more_than_the_limit(book):
    ranked = top_products(book.open_orders(), limit=1)
    assert len(ranked) == 1


def test_top_products_ignores_cancelled_orders(book):
    for order in book.open_orders():
        book.cancel(order.id)
    assert top_products(list(book.in_state("CANCELLED"))) == []


def test_rollups_bucket_by_day(book):
    for order in list(book.open_orders()):
        book.cancel(order.id)
    rollups = daily_rollups(book)
    assert len(rollups) == 1
    assert rollups[0].cancelled == 3


def test_fulfilment_rate_of_an_empty_book_is_zero():
    assert fulfilment_rate(OrderBook()) == 0.0
