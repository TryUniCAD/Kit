from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Blind.ReadEndDepth import (
    ReadEndDepth,
)


# blind construction needs authored depth direction and target version before any archive node exists
@DataClass(frozen=True, slots=True)
class BlindEndInput:
    DepthValue: float
    IsReversed: bool
    VersionValue: int

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
