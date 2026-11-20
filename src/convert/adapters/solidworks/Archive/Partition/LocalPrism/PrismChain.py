from collections.abc import Iterable

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismRef


# linked records require null endpoints and reciprocal consecutive links
def PrismChain(
    References: Iterable[PrismRef],
) -> dict[PrismRef, tuple[PrismRef | int, PrismRef | int]]:
    OrderValues = tuple(References)
    LinksValue: dict[PrismRef, tuple[PrismRef | int, PrismRef | int]] = {}
    for IndexValue, RefValue in enumerate(OrderValues):
        Previous = OrderValues[IndexValue - 1] if IndexValue else 0
        Following = (
            OrderValues[IndexValue + 1] if IndexValue + 1 < len(OrderValues) else 0
        )
        LinksValue[RefValue] = (Previous, Following)
    return LinksValue
