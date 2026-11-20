from __future__ import annotations

from math import isfinite as IsFinite
from typing import TYPE_CHECKING as TypeChecking, cast as CastValue

from convert.adapters.solidworks.Archive.Definition.Construction.RequireDefNumber import (
    RequireDefNum,
)
from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)

if TypeChecking:
    from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
        LightInput,
    )


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
