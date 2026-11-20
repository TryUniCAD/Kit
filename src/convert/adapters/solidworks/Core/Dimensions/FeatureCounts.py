from __future__ import annotations

from typing import TYPE_CHECKING

import struct as Struct

from convert.adapters.solidworks.Core.Dimensions.CountFields import CountFields

if TYPE_CHECKING:
    from convert.adapters.solidworks.Core.Native import NativeName, XmlFeature


# count handles need independently qualified copies before their native scalar can be exported
def FeatureCounts(
    Resolved: bytes,
    XmlFeatures: list[XmlFeature],
    Names: tuple[NativeName, ...],
    Copies: tuple[int, ...],
) -> dict[tuple[int, str], tuple[int, int]]:
    Counts: dict[tuple[int, str], tuple[int, int]] = {}
    if not Copies:
        return Counts
    for Owner, _, Dimension, Scalar, EndOffset in CountFields(
        Resolved, XmlFeatures, Names
    ):
        if Scalar + Copies[-1] + 8 > EndOffset:
            continue
        Values = {
            Struct.unpack_from("<d", Resolved, Scalar + Offset)[0] for Offset in Copies
        }
        if len(Values) != 1:
            continue
        Value = Values.pop()
        if not Value.is_integer() or not 0 < Value < 2**32:
            continue
        if any(
            int.from_bytes(Resolved[Scalar : Scalar + Width], "little") == Value
            for Width in (1, 2, 4, 8)
        ):
            Counts[Owner, Dimension.name] = (int(Value), Scalar + Copies[0])
    return Counts
