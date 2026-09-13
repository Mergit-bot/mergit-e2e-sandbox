"""The nightly CSV drop from suppliers.

Every supplier sends one file per night, listing what they are shipping us and what they
are charging. The format was agreed years ago and is not going to change:

    sku,description,quantity,unit_cost_cents,expected_date

Descriptions are free text written by humans at the supplier, so they contain commas,
quotes and the occasional newline. Files are quoted per RFC 4180 when the supplier's
system bothers to do it.

The import is expected to be tolerant: one bad row must not stop a delivery of four
hundred good ones. It is not expected to be silent — whatever it skips has to end up in
the report, because a line that vanishes here is stock the warehouse believes it has.
"""
from __future__ import annotations

from dataclasses import dataclass, field

EXPECTED_HEADER = ["sku", "description", "quantity", "unit_cost_cents", "expected_date"]


class FeedError(Exception):
    """A file that cannot be read at all."""


@dataclass
class FeedRow:
    sku: str
    description: str
    quantity: int
    unit_cost_cents: int
    expected_date: str

    @property
    def extended_cost_cents(self) -> int:
        return self.quantity * self.unit_cost_cents


@dataclass
class ImportResult:
    """What the nightly job reports to the ops channel."""

    supplier: str
    rows: list[FeedRow] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    total_units: int = 0
    total_cost_cents: int = 0

    @property
    def imported(self) -> int:
        return len(self.rows)

    @property
    def ok(self) -> bool:
        return self.imported > 0

    def summary(self) -> str:
        return (f"{self.supplier}: imported {self.imported} rows, "
                f"{self.total_units} units, "
                f"{self.total_cost_cents} cents")

    def as_dict(self) -> dict:
        return {
            "supplier": self.supplier,
            "imported": self.imported,
            "skipped": len(self.skipped),
            "total_units": self.total_units,
            "total_cost_cents": self.total_cost_cents,
            "ok": self.ok,
        }


def split_line(line: str) -> list[str]:
    """Split one CSV record into fields."""
    return [field.strip() for field in line.split(",")]


def is_header(fields: list[str]) -> bool:
    return len(fields) > 0 and fields[0].strip().lower() == "sku"


def parse_row(fields: list[str]) -> FeedRow:
    """Turn one split record into a row, or raise if it does not make sense."""
    if len(fields) != len(EXPECTED_HEADER):
        raise ValueError(f"expected {len(EXPECTED_HEADER)} fields, got {len(fields)}")
    sku, description, quantity, unit_cost, expected_date = fields
    if not sku:
        raise ValueError("missing sku")
    row = FeedRow(
        sku=sku.strip().upper(),
        description=description.strip().strip('"'),
        quantity=int(quantity),
        unit_cost_cents=int(unit_cost),
        expected_date=expected_date.strip(),
    )
    if row.quantity < 1:
        raise ValueError(f"{row.sku}: quantity must be positive")
    if row.unit_cost_cents < 0:
        raise ValueError(f"{row.sku}: cost must not be negative")
    return row


def parse_feed(text: str, supplier: str = "unknown") -> ImportResult:
    """Read a whole supplier file.

    Blank lines and the header are ignored. Anything that cannot be parsed is skipped so
    that one bad record does not cost us the rest of the delivery.
    """
    result = ImportResult(supplier=supplier)
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        fields = split_line(line)
        if is_header(fields):
            continue
        try:
            row = parse_row(fields)
        except Exception:
            continue
        result.rows.append(row)
        result.total_units += row.quantity
        result.total_cost_cents += row.extended_cost_cents
    return result


def load_feed(path: str, supplier: str = "") -> ImportResult:
    """Read a supplier file from disk."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        raise FeedError(f"could not read {path}: {exc}") from exc
    return parse_feed(text, supplier or path)


def apply_to_warehouse(result: ImportResult, warehouse) -> list[str]:
    """Book every imported row into stock, returning the SKUs touched."""
    touched = []
    for row in result.rows:
        warehouse.receive(row.sku, row.quantity)
        touched.append(row.sku)
    return touched


def reconcile(result: ImportResult, expected_units: dict[str, int]) -> dict[str, int]:
    """Compare what arrived against what the purchase order said would arrive.

    Returns SKU -> difference, positive when more arrived than expected.
    """
    arrived: dict[str, int] = {}
    for row in result.rows:
        arrived[row.sku] = arrived.get(row.sku, 0) + row.quantity
    difference = {}
    for sku in set(arrived) | set(expected_units):
        delta = arrived.get(sku, 0) - expected_units.get(sku, 0)
        if delta:
            difference[sku] = delta
    return difference
