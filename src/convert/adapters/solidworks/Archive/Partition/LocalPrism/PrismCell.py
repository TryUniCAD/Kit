from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismVectors import (
    KPrismVector,
)


# the neutral key needs a kernel class to distinguish an entity from its carrier
@DataClass(frozen=True, slots=True)
class PrismRef:
    KindValue: int
    IdValue: str


# draft links are distinct from measured scalar and geometry values
KPrismCellValue = PrismRef | int | float | str | KPrismVector


# local cells retain symbolic ownership until all transmit indices can be allocated
@DataClass(frozen=True, slots=True)
class PrismCell:
    RefValue: PrismRef
    FieldsValue: Mapping[str, KPrismCellValue]
