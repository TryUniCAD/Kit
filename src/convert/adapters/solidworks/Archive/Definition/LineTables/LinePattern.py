from dataclasses import dataclass as DataClass
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar


# native line patterns need authored names and signed segments instead of saved default rows
@DataClass(frozen=True, slots=True)
class LinePattern:
    NameValue: str
    CaptionValue: str
    SegmentsValue: tuple[float, ...]
    ThickThinValue: bool

    # this profile admits finite nonzero periods and the ordinary constructor plus thick thin setter
    def __post_init__(self) -> None:
        if not ReadStyleText(self.NameValue, "line pattern name") or not ReadStyleText(
            self.CaptionValue, "line pattern caption"
        ):
            raise ValueError("line pattern names must be nonempty")
        if (
            type(CastValue(object, self.SegmentsValue)) is not tuple
            or not 1 <= len(self.SegmentsValue) <= 0xFFFF
        ):
            raise ValueError("line pattern needs one to unsigned16 signed segments")
        Segments = tuple(RequireScalar(Value) for Value in self.SegmentsValue)
        PeriodValue = sum(abs(Value) for Value in Segments)
        if not IsFinite(PeriodValue) or PeriodValue <= 0:
            raise ValueError("line pattern period must be finite and positive")
        if type(CastValue(object, self.ThickThinValue)) is not bool:
            raise TypeError("line pattern thick thin state must be boolean")
        object.__setattr__(self, "SegmentsValue", Segments)
