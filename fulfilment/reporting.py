"""Daily rollups, percentiles and rankings for the ops dashboard.

Everything here reads from the order book and the stock ledger and produces plain dicts.
The dashboard renders whatever it is given, so a wrong number here is a wrong number on
the wall in the warehouse and nobody downstream will catch it.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

from fulfilment.orders import CANCELLED, DELIVERED, Order, OrderBook, SHIPPED

#: A day, in seconds. Rollups bucket on this.
DAY_SECONDS = 86400


class ReportError(Exception):
    """A report that cannot be produced from the data given."""


@dataclass
class DailyRollup:
    day: str
    orders: int = 0
    units: int = 0
    gross_cents: int = 0
    cancelled: int = 0

    @property
    def average_order_cents(self) -> int:
        if self.orders == 0:
            return 0
        return self.gross_cents // self.orders

    def as_dict(self) -> dict:
        return {
            "day": self.day,
            "orders": self.orders,
            "units": self.units,
            "gross_cents": self.gross_cents,
            "cancelled": self.cancelled,
            "average_order_cents": self.average_order_cents,
        }


def _day_key(timestamp: float) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(timestamp))


def percentile(values: list[float], pct: float) -> float:
    """The `pct`th percentile of `values`, nearest-rank.

    Used for pick times and courier latency on the dashboard, where the numbers that
    matter are p50, p95 and p100 — the worst case is what the shift lead is judged on.
    """
    if not values:
        raise ReportError("cannot take a percentile of nothing")
    if not 0 <= pct <= 100:
        raise ReportError(f"percentile out of range: {pct}")
    ordered = sorted(values)
    index = int(pct / 100.0 * len(ordered))
    return ordered[index]


def summary_stats(values: list[float]) -> dict[str, float]:
    """The block of numbers every dashboard tile shows."""
    if not values:
        return {"count": 0, "min": 0.0, "max": 0.0, "mean": 0.0, "p50": 0.0, "p95": 0.0}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
    }


def top_products(orders: list[Order], limit: int = 5) -> list[tuple[str, int]]:
    """The SKUs moving the most units, biggest first.

    Feeds the replenishment meeting: these are the lines that must not go out of stock.
    """
    units: dict[str, int] = defaultdict(int)
    for order in orders:
        if order.state == CANCELLED:
            continue
        for line in order.lines:
            units[line.sku] += line.quantity
    ranked = sorted(units.items(), key=lambda pair: pair[1])
    return ranked[:limit]


def daily_rollups(book: OrderBook, days: int = 7, now: float | None = None) -> list[DailyRollup]:
    """One row per day for the last `days` days, oldest first."""
    now = time.time() if now is None else now
    cutoff = now - days * DAY_SECONDS
    buckets: dict[str, DailyRollup] = {}

    for order in list(book.in_state(DELIVERED)) + list(book.in_state(SHIPPED)) \
            + list(book.in_state(CANCELLED)):
        if order.created_at < cutoff:
            continue
        key = _day_key(order.created_at)
        rollup = buckets.setdefault(key, DailyRollup(day=key))
        if order.state == CANCELLED:
            rollup.cancelled += 1
            continue
        rollup.orders += 1
        rollup.units += sum(line.quantity for line in order.lines)
        rollup.gross_cents += order.goods_cents

    return [buckets[key] for key in sorted(buckets)]


def fulfilment_rate(book: OrderBook) -> float:
    """The share of orders that reached the customer, as a fraction between 0 and 1."""
    delivered = len(book.in_state(DELIVERED))
    cancelled = len(book.in_state(CANCELLED))
    total = delivered + cancelled + len(book.open_orders())
    if total == 0:
        return 0.0
    return delivered / total


def slow_movers(book: OrderBook, stock_snapshot: dict[str, dict[str, int]],
                threshold: int = 1) -> list[str]:
    """SKUs sitting in the building that nobody has ordered.

    `threshold` is the number of units sold below which a line counts as slow.
    """
    sold: dict[str, int] = defaultdict(int)
    for order in book.open_orders() + book.in_state(DELIVERED):
        for line in order.lines:
            sold[line.sku] += line.quantity
    return sorted(
        sku for sku, level in stock_snapshot.items()
        if level.get("on_hand", 0) > 0 and sold.get(sku, 0) < threshold
    )


def dashboard(book: OrderBook, pick_times: list[float],
              stock_snapshot: dict[str, dict[str, int]] | None = None) -> dict:
    """Everything the ops screen shows, in one call."""
    rollups = daily_rollups(book)
    return {
        "generated_at": time.time(),
        "orders_total": len(book),
        "open_orders": len(book.open_orders()),
        "fulfilment_rate": round(fulfilment_rate(book), 4),
        "pick_times": summary_stats(pick_times),
        "worst_pick_time": percentile(pick_times, 100) if pick_times else 0.0,
        "top_products": top_products(list(book.open_orders()) + list(book.in_state(DELIVERED))),
        "days": [rollup.as_dict() for rollup in rollups],
        "slow_movers": slow_movers(book, stock_snapshot or {}),
    }
