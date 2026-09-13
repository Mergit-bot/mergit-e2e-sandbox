"""Products, SKUs and the discount tiers attached to them.

The catalog is loaded once at start-up and treated as read-only for the lifetime of the
process. Prices are held in whole cents — every module downstream is expected to keep
money in integers for as long as it can, and to convert only at the edges where a human
or an invoice needs to read it.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class CatalogError(Exception):
    """A product or SKU that does not exist, or a catalog that does not make sense."""


@dataclass(frozen=True)
class Tier:
    """A quantity break: buy `min_quantity` or more, pay `unit_price_cents` each.

    Tiers belong to a product and are held in ascending order of `min_quantity`. The
    first tier of every product starts at 1 and carries the list price, so there is
    always a tier that applies to any positive quantity.
    """

    min_quantity: int
    unit_price_cents: int

    def __post_init__(self) -> None:
        if self.min_quantity < 1:
            raise CatalogError(f"tier min_quantity must be positive, got {self.min_quantity}")
        if self.unit_price_cents < 0:
            raise CatalogError(f"tier price must not be negative, got {self.unit_price_cents}")


@dataclass
class Product:
    """One sellable thing.

    `weight_grams` is the shipping weight of a single unit and is used by the courier
    quote; `hazmat` products are excluded from air freight and from the express tier.
    """

    sku: str
    name: str
    list_price_cents: int
    weight_grams: int
    category: str = "general"
    hazmat: bool = False
    tiers: list[Tier] = field(default_factory=list)
    active: bool = True

    def __post_init__(self) -> None:
        if not self.sku:
            raise CatalogError("a product needs a SKU")
        if self.list_price_cents < 0:
            raise CatalogError(f"{self.sku}: list price must not be negative")
        if not self.tiers:
            self.tiers = [Tier(min_quantity=1, unit_price_cents=self.list_price_cents)]
        self.tiers.sort(key=lambda t: t.min_quantity)
        if self.tiers[0].min_quantity != 1:
            raise CatalogError(f"{self.sku}: the first tier must start at quantity 1")


class Catalog:
    """Every product the warehouse sells, indexed by SKU."""

    def __init__(self, products: list[Product] | None = None) -> None:
        self._by_sku: dict[str, Product] = {}
        for product in products or []:
            self.add(product)

    def add(self, product: Product) -> None:
        if product.sku in self._by_sku:
            raise CatalogError(f"duplicate SKU: {product.sku}")
        self._by_sku[product.sku] = product

    def get(self, sku: str) -> Product:
        try:
            return self._by_sku[sku]
        except KeyError:
            raise CatalogError(f"no such SKU: {sku}") from None

    def has(self, sku: str) -> bool:
        return sku in self._by_sku

    def active_products(self) -> list[Product]:
        return [p for p in self._by_sku.values() if p.active]

    def by_category(self, category: str) -> list[Product]:
        return [p for p in self._by_sku.values() if p.category == category and p.active]

    def __len__(self) -> int:
        return len(self._by_sku)

    def __contains__(self, sku: object) -> bool:
        return isinstance(sku, str) and sku in self._by_sku


def demo_catalog() -> Catalog:
    """The fixture the tests and the REPL share.

    Roughly models the real thing: a couple of fast movers with deep quantity breaks, a
    heavy item, a hazmat item and one discontinued line.
    """
    return Catalog([
        Product(
            sku="WID-100", name="Widget, standard", list_price_cents=1299,
            weight_grams=250, category="widgets",
            tiers=[
                Tier(min_quantity=1, unit_price_cents=1299),
                Tier(min_quantity=10, unit_price_cents=1199),
                Tier(min_quantity=50, unit_price_cents=999),
                Tier(min_quantity=250, unit_price_cents=899),
            ],
        ),
        Product(
            sku="WID-200", name="Widget, reinforced", list_price_cents=2450,
            weight_grams=700, category="widgets",
            tiers=[
                Tier(min_quantity=1, unit_price_cents=2450),
                Tier(min_quantity=25, unit_price_cents=2250),
                Tier(min_quantity=100, unit_price_cents=1975),
            ],
        ),
        Product(
            sku="GRM-010", name="Grommet, brass", list_price_cents=349,
            weight_grams=30, category="fittings",
            tiers=[
                Tier(min_quantity=1, unit_price_cents=349),
                Tier(min_quantity=100, unit_price_cents=299),
                Tier(min_quantity=1000, unit_price_cents=249),
            ],
        ),
        Product(
            sku="ANV-001", name="Anvil, 50kg", list_price_cents=18900,
            weight_grams=50000, category="heavy",
        ),
        Product(
            sku="SOL-050", name="Solvent, 5L", list_price_cents=4200,
            weight_grams=5200, category="chemicals", hazmat=True,
        ),
        Product(
            sku="WID-050", name="Widget, legacy", list_price_cents=899,
            weight_grams=240, category="widgets", active=False,
        ),
    ])
