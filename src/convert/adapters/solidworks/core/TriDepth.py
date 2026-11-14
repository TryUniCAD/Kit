from __future__ import annotations

from dataclasses import replace as Replace
import math as MathValue
import struct as Struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from convert.adapters.solidworks.core.Native import NativeDimension, NativeSketch

KSourceLength = 10601
KPositiveOffsets = (9408, 9480, 9968, 9992)
KNegativeOffsets = (9806, 9830)


def RecoverTriDepth(
    DataValue: bytes, Sketch: NativeSketch | None, Dimension: NativeDimension
) -> NativeDimension | None:
    if (
        len(DataValue) not in {10601, 10603}
        or Sketch is None
        or len(Sketch.profiles) != 1
        or Sketch.profiles[0].kind != "polyline"
        or len(Sketch.profiles[0].coordinates) != 6
        or Dimension.name != "D1"
        or Dimension.kind != "length"
        or Dimension.native_value is not None
    ):
        return None
    Shift = len(DataValue) - KSourceLength
    Positive = tuple(
        Struct.unpack_from("<d", DataValue, Offset + Shift)[0]
        for Offset in KPositiveOffsets
    )
    Negative = tuple(
        Struct.unpack_from("<d", DataValue, Offset + Shift)[0]
        for Offset in KNegativeOffsets
    )
    if (
        len(set(Positive)) != 1
        or Negative != (-Positive[0], -Positive[0])
        or not MathValue.isfinite(Positive[0])
        or Positive[0] <= 0.0
    ):
        return None
    ValueMm = Positive[0] * 1000.0
    if not MathValue.isclose(
        ValueMm, Dimension.value_mm, rel_tol=0.0, abs_tol=0.005000001
    ):
        return None
    return Replace(
        Dimension,
        value_mm=ValueMm,
        native_value=Positive[0],
        native_offset=KPositiveOffsets[0] + Shift,
        native_role="driving",
    )
