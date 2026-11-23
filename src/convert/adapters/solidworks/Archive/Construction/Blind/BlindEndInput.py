from dataclasses import dataclass as DataClass
from dataclasses import field as MakeDataField
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Blind.ReadEndDepth import (
    ReadEndDepth,
)

from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadDriverName import (
    ReadDriverName,
)


# one direction construction needs to retain an independently authored dormant depth without changing its geometric mode
@DataClass(frozen=True, slots=True)
class BlindEndInput:
    DepthValue: float
    IsReversed: bool
    VersionValue: int
    DepthName: str = "D1"
    DormantDepth: float | None = MakeDataField(default=None, kw_only=True)

    # invalid dimensions must fail before constructor state can be mistaken for native output
    def __post_init__(self) -> None:
        if (
            type(CastValue(object, self.VersionValue)) is not int
            or self.VersionValue != 19000
        ):
            raise ValueError("blind construction requires archive version 19000")
        if type(CastValue(object, self.IsReversed)) is not bool or self.IsReversed:
            raise ValueError(
                "blind construction currently requires the forward direction"
            )
        _ = ReadEndDepth(self.DepthValue)
        if self.DormantDepth is not None:
            _ = ReadEndDepth(self.DormantDepth)
        _ = ReadDriverName(self.DepthName)
