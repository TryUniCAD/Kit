from __future__ import annotations as Annotations
from convert.adapters.base.NativeEvidence import KUnresolvedInchDimension as KUnresolvedInchDimension

from dataclasses import replace as Replace
from typing import Mapping

from convert.adapters.solidworks.Core.Inch.InchDecimal import InchDecimal
from convert.adapters.solidworks.Core.Inch.InchScalar import IsRoundedInch
from interchange.Features.DistanceParam import KLengthFactors

from convert.adapters.solidworks.Core.NativeDimension import NativeDimension
from convert.adapters.solidworks.Core.NativeScalar import NativeScalar



# binary scalars preserve authored lengths when the display number is rounded
def BindInch(
    Dimension: NativeDimension,
    ScalarsByName: Mapping[str, tuple[NativeScalar, ...]],
    Decimals: int | None,
) -> NativeDimension:
    Displayed = InchDecimal(Dimension.source_text)
    Unresolved = Replace(
        Dimension,
        value_mm=None,
        inch_display_value=Displayed[0] if Displayed is not None else None,
    )
    Named = ScalarsByName.get(Dimension.name, ())
    if (
        not Dimension.name
        or Decimals is None
        or Displayed is None
        or Displayed[1] > Decimals
        or len(Named) != 1
    ):
        return Unresolved
    Scalar = Named[0]
    if (
        Scalar.object_id is None
        or Scalar.role not in {"driving", "native"}
        or not IsRoundedInch(Displayed[0], Scalar.value, Decimals)
    ):
        return Unresolved
    return Replace(
        Dimension,
        value_mm=Scalar.value * KLengthFactors["m"],
        native_value=Scalar.value,
        native_offset=Scalar.value_offset,
        native_role=Scalar.role,
        operands=Scalar.operands,
        inch_display_value=None,
    )
