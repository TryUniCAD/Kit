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

    # unknown suffix grammar and nonfinite quantities must fail before formatting loses their original semantic meaning
    def __post_init__(self) -> None:
        _ = ReadStyleText(self.NameValue, "keyword dimension name")
        _ = ReadStyleNum(self.NumberValue, "keyword dimension value")
        if self.UnitValue not in (None, "degree"):
            raise ValueError(
                "keyword dimension unit suffix is classified only for ordinary revolve degrees"
            )
