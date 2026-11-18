from dataclasses import dataclass as DataClass
from typing import Literal

from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)


# explicit selected stock intent must retain its actual owner instead of implying continuous automatic selection
@DataClass(frozen=True, slots=True)
class SelectedStock:
    StockValues: tuple[ThroughStock, ...]
    ModeValue: Literal["selected"]
    VersionValue: int

    # missing ambiguous or automatic scope must fail before a native graph is constructed
    def __post_init__(self) -> None:
        if (
            type(self.StockValues) is not tuple
            or len(self.StockValues) != 1
            or type(self.StockValues[0]) is not ThroughStock
        ):
            raise ValueError(
                "selected stock requires exactly one actual typed stock owner"
            )
        if type(self.ModeValue) is not str or self.ModeValue != "selected":
            raise ValueError(
                "continuous automatic selection is outside the selected stock constructor"
            )
        if type(self.VersionValue) is not int or self.VersionValue != 19000:
            raise ValueError(
                "selected stock is qualified only for archive version 19000"
            )
        ReadStyleText(self.StockValues[0].BodyId, "selected stock body identity")
        ReadStyleText(
            self.StockValues[0].FeatureId, "selected stock producing feature identity"
        )
