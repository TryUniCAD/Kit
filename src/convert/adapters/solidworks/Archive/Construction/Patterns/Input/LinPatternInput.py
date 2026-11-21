from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.AnglePlaneInput import (
    AnglePlaneInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.SeedStockInput import (
    SeedStockInput,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)


# native pattern construction needs the owned stock datum and presentation controls together
@DataClass(frozen=True, slots=True)
class LinPatternInput:
    StockValue: SeedStockInput
    HingeName: str
    AngleValue: AnglePlaneInput
    AnnoValues: tuple[AnnoViewInput, ...]
    ActiveAnno: str | None
    ShownAnnos: tuple[str | None, ...]
    NameValue: str
    CountValue: int
    PitchValue: float
    Reversed: bool
    StyleValues: tuple[PatDriveStyle, ...]
