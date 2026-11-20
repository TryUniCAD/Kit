from dataclasses import replace as Replace
from decimal import Decimal, ROUND_HALF_UP
from math import isfinite as IsFinite
from re import fullmatch as FullMatch

from convert.adapters.solidworks.Core.LinearDisplay import LinearDisplay
from convert.adapters.solidworks.Core.NativeDimension import NativeDimension
from convert.adapters.solidworks.Core.NativeScalar import NativeScalar


# paired records with the same operands preserve a sketch length beyond its printed precision
def PairedSketchLength(
    Dimension: NativeDimension,
    Scalars: tuple[NativeScalar, ...],
    Display: LinearDisplay | None,
    Stream: str,
) -> NativeDimension:
    if (
        Dimension.kind != "length"
        or not Display
        or Display.UnitName != "mm"
        or Display.Decimals is None
        or not 0 <= Display.Decimals <= 12
        or not FullMatch(
            r"[+-]?[0-9]{1,12}(?:[.][0-9]{1,12})?", Dimension.source_text.strip()
        )
    ):
        return Dimension
    if len(Scalars) != 2:
        return Dimension
    Copy, Driving = Scalars if Scalars[0].role == "display" else reversed(Scalars)
    if (
        (Copy.role, Driving.role) != ("display", "driving")
        or Copy.object_id is None
        or Driving.object_id is None
        or Copy.object_id == Driving.object_id
        or Copy.value != Driving.value
        or not IsFinite(Driving.value)
        or abs(Driving.value) >= 1e9
        or not Driving.operands
        or tuple((Op.kind_code, Op.entity_index) for Op in Driving.operands)
        != tuple((Op.kind_code, Op.entity_index) for Op in Copy.operands)
    ):
        return Dimension
    if Dimension.native_offset == Driving.value_offset and Dimension.native_role == "driving":
        return Dimension
    Measured = Decimal(str(Driving.value)) * 1000
    if Measured.quantize(
        Decimal(1).scaleb(-Display.Decimals), rounding=ROUND_HALF_UP
    ) != Decimal(Dimension.source_text.strip()):
        return Dimension
    return Replace(
        Dimension,
        value_mm=float(Measured),
        native_value=Driving.value,
        native_role=Driving.role,
        native_offset=Driving.value_offset,
        native_stream=Stream,
        operands=Driving.operands,
    )
