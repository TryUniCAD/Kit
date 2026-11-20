from __future__ import annotations
from bisect import bisect_right as BisectRight
from collections import defaultdict as DefaultDict
from typing import TYPE_CHECKING

from convert.adapters.solidworks.Core.Dimensions.ReadCountParam import ReadCountParam
from convert.adapters.solidworks.Core.Dimensions.JoinCountPairs import JoinCountPairs

if TYPE_CHECKING:
    from convert.adapters.solidworks.Core.Native import (
        NativeClass,
        NativeName,
        XmlFeature,
    )


# count parameters and handles must share a feature interval and pattern family
def PatternPairs(
    DataValue: bytes,
    Features: list[XmlFeature],
    Names: tuple[NativeName, ...],
    Classes: tuple[NativeClass, ...],
) -> list[tuple[int, str, str, int, int, int, int, int]]:
    Owners = {Feature.object_id: Feature.name for Feature in Features}
    if len(Owners) != len(Features):
        return []
    Markers = sorted(
        (ItemValue.offset, ItemValue.object_id)
        for ItemValue in Names
        if ItemValue.object_id in Owners
        and Owners[ItemValue.object_id] == ItemValue.name
    )
    Offsets = [Offset for Offset, _ in Markers]
    if len(set(Offsets)) != len(Offsets):
        return []
    Parameters, Handles = DefaultDict(list), DefaultDict(list)
    for Index, Record in enumerate(Classes):
        Marker = BisectRight(Offsets, Record.offset) - 1
        if Marker < 0:
            continue
        OwnerKey = (Marker, Record.name)
        EndOffset = Offsets[Marker + 1] if Marker + 1 < len(Offsets) else len(DataValue)
        Cursor = Record.offset + 6 + len(Record.name)
        if Record.name in (
            "moSkDimHandleCircularPattCnt_c",
            "moSkDimHandleLinearPattCnt_c",
        ):
            EndOffset = min(
                EndOffset,
                Classes[Index + 1].offset if Index + 1 < len(Classes) else EndOffset,
            )
            Handles[OwnerKey].append(
                (Record.offset, Cursor, min(EndOffset, Cursor + 1024))
            )
            continue
        Parameter = ReadCountParam(
            DataValue,
            Record,
            Cursor,
            EndOffset,
            Classes[Index + 1] if Index + 1 < len(Classes) else None,
        )
        if Parameter is not None:
            Parameters[OwnerKey].append(Parameter)
    return JoinCountPairs(Parameters, Handles, Markers)
