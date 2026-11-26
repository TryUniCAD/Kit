from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Sketch.Validation.ValidateRing import (
    ValidateRing,
)


# explicit local coordinates and version prevent native construction from borrowing document defaults
@DataClass(frozen=True, slots=True)
class PolygonInput:
    VerticesValue: tuple[tuple[float, float], ...]
    VersionValue: int

    # invalid geometry must fail before an incomplete native graph can be created
    def __post_init__(self) -> None:
        if (
            type(CastValue(object, self.VersionValue)) is not int
            or self.VersionValue != 19000
        ):
            raise ValueError("polygon construction requires archive version 19000")
        object.__setattr__(self, "VerticesValue", ValidateRing(self.VerticesValue))
