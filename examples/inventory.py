"""Track stock levels, apply orders, and report items that need reordering."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    quantity: int
    reorder_level: int


class StockError(Exception):
    pass


def needs_reorder(item: Item) -> bool:
    return item.quantity <= item.reorder_level


def remove_stock(item: Item, amount: int) -> Item:
    if amount <= 0:
        raise StockError(f"amount must be positive, got {amount}")
    if amount > item.quantity:
        raise StockError(f"only {item.quantity} of {item.sku} in stock")
    return Item(item.sku, item.name, item.quantity - amount, item.reorder_level)


def apply_order(stock: dict[str, Item], sku: str, amount: int) -> dict[str, Item]:
    if sku not in stock:
        raise StockError(f"unknown item {sku}")
    updated = dict(stock)
    updated[sku] = remove_stock(stock[sku], amount)
    return updated


def reorder_report(stock: dict[str, Item]) -> list[str]:
    low = [item for item in stock.values() if needs_reorder(item)]
    ordered = sorted(low, key=lambda item: item.quantity)
    return [f"{item.sku}  {item.name:<10} {item.quantity:>3} left" for item in ordered]


def main() -> None:
    stock = {
        "A100": Item("A100", "bolts", 40, 10),
        "B200": Item("B200", "washers", 12, 15),
        "C300": Item("C300", "hinges", 8, 5),
    }
    orders = [("A100", 35), ("B200", 5), ("C300", 99), ("D400", 1)]
    for sku, amount in orders:
        try:
            stock = apply_order(stock, sku, amount)
        except StockError as error:
            print(f"rejected order for {sku}: {error}")
    print("reorder:")
    for line in reorder_report(stock):
        print(f"  {line}")


if __name__ == "__main__":
    main()
