from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue


def CheckMaterial(SpecValue: MaterialSpec) -> None:
    if not isinstance(CastValue(object, SpecValue), MaterialSpec):
        raise ValueError("A typed authored material specification is required")
    if (
        not isinstance(CastValue(object, SpecValue.NameValue), str)
        or not SpecValue.NameValue
        or len(SpecValue.NameValue) > 1024
        or "\x00" in SpecValue.NameValue
    ):
        raise ValueError("Invalid authored material name")
    if (
        type(SpecValue.Density) not in (int, float)
        or not IsFinite(SpecValue.Density)
        or not 0 < SpecValue.Density <= 25000
    ):
        raise ValueError("Material density must be positive and at most 25000 kg/m3")
    if not isinstance(CastValue(object, SpecValue.Color), ColorValue):
        raise ValueError("A typed material RGBA color is required")
    for Channel in (
        SpecValue.Color.RedValue,
        SpecValue.Color.GreenValue,
        SpecValue.Color.BlueValue,
        SpecValue.Color.AlphaValue,
    ):
        if (
            type(Channel) not in (int, float)
            or not IsFinite(Channel)
            or not 0 <= Channel <= 1
        ):
            raise ValueError(
                "Material color channels must be finite between zero and one"
            )
