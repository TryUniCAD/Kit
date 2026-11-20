from dataclasses import replace as Replace
from math import degrees as Degrees, isclose as IsClose
from re import fullmatch as FullMatch
from struct import unpack_from as UnpackFrom

from convert.adapters.solidworks.Core.LinearDisplay import LinearDisplay
from convert.adapters.solidworks.Core.NativeDimension import NativeDimension
from convert.adapters.solidworks.Core.NativeScalar import NativeScalar

# independent document replay qualifies the signed copies for each typed field
KMirroredFields: dict[tuple[str, str, str], tuple[tuple[int, int], ...]] = {}


# angular text can round a saved value to the number of printed decimal places
def MatchesAngle(SourceText: str, Displayed: float, Measured: float) -> bool:
    if IsClose(Displayed, Measured, rel_tol=1e-12, abs_tol=1e-12):
        return True
    Match = FullMatch(r"[+-]?[0-9]+\.([0-9]{1,12})\s*(?:°|deg)", SourceText.strip())
    return Match is not None and abs(Displayed - Measured) < 0.5 * 10 ** -len(Match[1])


# a named scalar and every bounded mirror must agree before refining a public measurement
def BindMirroredField(
    DataValue: bytes,
    End: int,
    Stream: str,
    Raw: NativeDimension,
    Bound: NativeDimension,
    Candidates: tuple[NativeScalar, ...],
    Copies: tuple[tuple[int, int], ...],
    Display: LinearDisplay | None,
) -> NativeDimension:
    Named = [Item for Item in Candidates if Item.name == Raw.name]
    if len(Named) != 1 or Raw.value_mm is None:
        return Bound
    Scalar = Named[0]
    if Scalar.value == 0 or any(
        Scalar.value_offset + Offset + 8 > End
        or UnpackFrom("<d", DataValue, Scalar.value_offset + Offset)[0] * Sign
        != Scalar.value
        for Offset, Sign in Copies
    ):
        return Bound
    if Raw.kind == "angle" and Bound.kind == "angle":
        Measured = Degrees(Scalar.value)
        if not MatchesAngle(Raw.source_text, Raw.value_mm, Measured):
            return Bound
    elif (
        Raw.kind != "angle"
        and Bound.kind
        in {
            "length",
            "spacing",
            "depth",
            "radius",
            "diameter",
            "offset",
            "thickness",
            "height",
        }
        and Display
        and Display.UnitName == "mm"
    ):
        Measured = Scalar.value * 1000
        if not IsClose(Raw.value_mm, Measured, rel_tol=1e-12, abs_tol=1e-12):
            return Bound
    else:
        return Bound
    return Replace(
        Bound,
        value_mm=(
            Raw.value_mm
            if IsClose(Measured, Raw.value_mm, rel_tol=1e-12, abs_tol=1e-12)
            else Measured
        ),
        native_value=Scalar.value,
        native_offset=Scalar.value_offset,
        native_role=Scalar.role,
        operands=Scalar.operands,
        native_stream=Stream,
    )
