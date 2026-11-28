from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import (
    SeedStockInput,
)


# the principal part supplies an existing plane role and the six explicit display styles
@DataClass(frozen=True, slots=True)
class PrincPatInput:
    StockValue: SeedStockInput
    AxisValue: str
    Reversed: bool
    NameValue: str
    CountValue: int
    PitchValue: float
    StyleValues: tuple[PatDriveStyle, ...]
