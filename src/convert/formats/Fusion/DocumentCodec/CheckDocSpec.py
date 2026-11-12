from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec


def CheckDocSpec(SpecValue: DocumentSpec) -> None:
    if not isinstance(CastValue(object, SpecValue), DocumentSpec):
        raise ValueError("A typed Fusion document specification is required")
    if SpecValue.ProfileKind not in ("parameter", "circle", "extrusion"):
        raise ValueError("Unsupported Fusion document profile")
    for Amount in (SpecValue.LengthMm, SpecValue.RadiusMm):
        if type(Amount) not in (int, float) or not IsFinite(Amount) or Amount <= 0:
            raise ValueError("Authored dimensions must be finite and positive")
    for TextValue in (
        SpecValue.Title,
        SpecValue.ParamName,
        SpecValue.ParamComment,
        SpecValue.SketchName,
        SpecValue.ExtrusionName,
        SpecValue.BodyName,
    ):
        if (
            not isinstance(CastValue(object, TextValue), str)
            or len(TextValue) > 1024
            or "\x00" in TextValue
        ):
            raise ValueError("Invalid authored document text")
    NameValue = SpecValue.ParamName
    if (
        not NameValue
        or not NameValue.isascii()
        or not NameValue.isidentifier()
        or NameValue in ("d2", "d3")
    ):
        raise ValueError("Unsupported authored parameter name")
