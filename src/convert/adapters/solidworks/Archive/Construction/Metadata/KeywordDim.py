from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# keyword dimensions must retain authored presentation units and cannot substitute an arbitrary scalar from a native saved row
@DataClass(frozen=True, slots=True)
class KeywordDim:
    NameValue: str
    NumberValue: int | float
    UnitValue: str | None
    PrefixValue: str | None = None
    PlacesValue: int | None = None

    # unknown suffix grammar and nonfinite quantities must fail before formatting loses their original semantic meaning
    def __post_init__(self) -> None:
        _ = ReadStyleText(self.NameValue, "keyword dimension name")
        _ = ReadStyleNum(self.NumberValue, "keyword dimension value")
        if self.UnitValue not in (None, "degree"):
            raise ValueError(
                "keyword dimension unit suffix is classified only for ordinary revolve degrees"
            )
        if self.PrefixValue not in (None, "radius", "diameter") or (
            self.PrefixValue is not None and self.UnitValue is not None
        ):
            raise ValueError(
                "keyword dimension modifier must identify a linear radius or diameter"
            )
        if self.PlacesValue is not None and (
            type(self.PlacesValue) is not int or not 0 <= self.PlacesValue <= 17
        ):
            raise ValueError(
                "keyword display precision must fit the fixed decimal grammar"
            )
