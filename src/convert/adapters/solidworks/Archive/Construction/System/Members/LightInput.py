from dataclasses import dataclass as DataClass
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Definition.Construction.RequireDefNumber import (
    RequireDefNum,
)


# explicit scene inputs prevent session defaults from becoming saved lighting seeds
@DataClass(frozen=True, slots=True)
class LightInput:
    KindValue: str
    NameValue: str
    ExternalName: str
    AmbientValue: float
    DiffuseValue: float
    SpecularValue: float
    ColourValue: int
    KeepInScene: bool
    EnabledInPv: bool
    UseCartesian: bool
    PvBrightness: float
    PvShadows: bool
    PvQuality: float
    DirectionValue: tuple[float, float, float] | None
    ShadowSoftness: float | None
    CreatedValue: FeatureInstant

    # invalid light semantics must fail before the shared model allocator is consumed
    def __post_init__(self) -> None:
        CheckLightInput(self)


# validated semantic domains keep unknown light kinds and nonfinite rendering state outside this component
def CheckLightInput(InputValue: LightInput) -> None:
    for TextValue in (InputValue.NameValue, InputValue.ExternalName):
        if not ReadStyleText(TextValue, "light identity"):
            raise ValueError("light names must be explicit nonempty text")
    for NumberValue in (
        InputValue.AmbientValue,
        InputValue.DiffuseValue,
        InputValue.SpecularValue,
    ):
        if (
            type(NumberValue) not in (int, float)
            or not IsFinite(NumberValue)
            or not 0 <= NumberValue <= 1
        ):
            raise ValueError("light coefficients require finite unit scalars")
    if (
        type(InputValue.ColourValue) is not int
        or not 0 <= InputValue.ColourValue < 1 << 24
    ):
        raise ValueError("light colour requires an explicit RGB COLORREF word")
    if any(
        type(ValueInput) is not bool
        for ValueInput in (
            InputValue.KeepInScene,
            InputValue.EnabledInPv,
            InputValue.UseCartesian,
            InputValue.PvShadows,
        )
    ):
        raise TypeError("light switches require explicit booleans")
    for NumberValue in (InputValue.PvBrightness, InputValue.PvQuality):
        if (
            type(NumberValue) not in (int, float)
            or not IsFinite(NumberValue)
            or NumberValue < 0
        ):
            raise ValueError(
                "light rendering values require finite nonnegative scalars"
            )
    if InputValue.KindValue == "ambient":
        if (
            InputValue.DirectionValue is not None
            or InputValue.ShadowSoftness is not None
        ):
            raise ValueError("ambient light has no directional subclass owners")
    elif InputValue.KindValue == "directional":
        Direction = InputValue.DirectionValue
        if (
            type(Direction) is not tuple
            or len(CastValue(tuple[object, ...], Direction)) != 3
            or any(
                type(ValueInput) not in (int, float) or not IsFinite(ValueInput)
                for ValueInput in Direction
            )
            or not any(Direction)
        ):
            raise ValueError("directional light requires a finite nonzero vector")
        Softness = RequireDefNum(InputValue.ShadowSoftness)
        if Softness < 0:
            raise ValueError(
                "directional shadow softness must be finite and nonnegative"
            )
    else:
        raise ValueError(
            "light kind is outside the mapped ambient and directional scope"
        )
    if type(InputValue.CreatedValue) is not FeatureInstant:
        raise TypeError("light creation requires a typed precise instant")
