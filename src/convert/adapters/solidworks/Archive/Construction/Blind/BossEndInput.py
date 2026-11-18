from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Blind.EndMode import KEndMode
from convert.adapters.solidworks.Archive.Construction.Blind.ReadEndDepth import (
    ReadEndDepth,
)


# the complete ordinary end specification keeps termination reversal and actual second direction independent
@DataClass(frozen=True, slots=True)
class BossEndInput:
    DepthValue: float
    IsReversed: bool
    VersionValue: int
    ModeValue: KEndMode
    SecondDepth: float | None = None

    # each supported condition must retain precisely its modeled active physical lengths
    def __post_init__(self) -> None:
        if (
            type(CastValue(object, self.VersionValue)) is not int
            or self.VersionValue != 19000
        ):
            raise ValueError("boss construction requires archive version 19000")
        if type(
            CastValue(object, self.IsReversed)
        ) is not bool or self.ModeValue not in ("blind", "mid_plane", "two_directions"):
            raise ValueError("boss termination and reversal require supported inputs")
        if (self.ModeValue == "two_directions") != (self.SecondDepth is not None):
            raise ValueError(
                "a two direction boss requires exactly its active second depth"
            )
        _ = ReadEndDepth(self.DepthValue)
        if self.SecondDepth is not None:
            _ = ReadEndDepth(self.SecondDepth)
