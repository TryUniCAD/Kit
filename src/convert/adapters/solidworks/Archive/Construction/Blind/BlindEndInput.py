from dataclasses import dataclass as DataClass
from math import isfinite as IsFinite
from typing import cast as CastValue


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
        if type(CastValue(object, self.IsReversed)) is not bool:
            raise ValueError("blind construction direction must be a boolean")
        if type(CastValue(object, self.DepthValue)) not in (int, float):
            raise TypeError("blind depth must be a real numeric input")
        try:
            NativeValue = float(self.DepthValue)
        except OverflowError as ErrorInfo:
            raise ValueError(
                "blind depth exceeds the native numeric domain"
            ) from ErrorInfo
        if not IsFinite(NativeValue) or NativeValue < 1e-14:
            raise ValueError("blind depth must be finite and at least 1e-14 metres")
