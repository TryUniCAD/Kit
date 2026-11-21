from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    FrontStockBox,
)


# the bounded merge needs two independent boxes and one actual part identity
@DataClass(frozen=True, slots=True)
class SeedStockInput:
    NameValue: str
    ConfigName: str
    PathValue: str
    SavedAt: int
    PlateValue: FrontStockBox
    SeedValue: FrontStockBox
