from __future__ import annotations
from bisect import bisect_right as BisectRight
from collections import defaultdict as DefaultDict
from typing import TYPE_CHECKING

from convert.adapters.solidworks.Container.Format import (
    SERIALIZED_STRING_MARKER as SerializedStringMarker,
    dimension_scalar_value_offset as DimensionScalarValue,
)

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
        (Item.offset, Item.object_id)
        for Item in Names
        if Item.object_id in Owners and Owners[Item.object_id] == Item.name
    )
    Offsets = [Offset for Offset, _ in Markers]
    if len(set(Offsets)) != len(Offsets):
        return []
    Parameters, Handles = DefaultDict(list), DefaultDict(list)
    for Index, Record in enumerate(Classes):
        Marker = BisectRight(Offsets, Record.offset) - 1
        if Marker < 0:
            continue
        Key = (Marker, Record.name)
        End = Offsets[Marker + 1] if Marker + 1 < len(Offsets) else len(DataValue)
        Cursor = Record.offset + 6 + len(Record.name)
        if Record.name in (
            "moSkDimHandleCircularPattCnt_c",
            "moSkDimHandleLinearPattCnt_c",
        ):
            End = min(
                End, Classes[Index + 1].offset if Index + 1 < len(Classes) else End
            )
            Handles[Key].append((Record.offset, Cursor, min(End, Cursor + 1024)))
            continue
        if Record.name not in (
            "sgCircularPattCntDim",
            "sgLinearPattCntDim",
        ) or DataValue[Cursor : Cursor + 4] != bytes(4):
            continue
        Cursor += 4
        Nested = Classes[Index + 1] if Index + 1 < len(Classes) else None
        if Nested and Nested.offset == Cursor and Nested.name == "moIntegerParameter_c":
            Cursor += 6 + len(Nested.name)
        elif (
            Cursor + 2 <= End
            and 0x8000
            <= int.from_bytes(DataValue[Cursor : Cursor + 2], "little")
            < 0xFFFF
        ):
            Cursor += 2
        else:
            continue
        if (
            Cursor + 6 > End
            or not int.from_bytes(DataValue[Cursor : Cursor + 2], "little") & 0x8000
        ):
            continue
        Cursor += 2
        if DataValue[Cursor : Cursor + 3] != SerializedStringMarker:
            continue
        Size = DataValue[Cursor + 3]
        if not 0 < Size < 255:
            continue
        TextEnd = Cursor + 4 + 2 * Size
        Scalar = DimensionScalarValue(DataValue, TextEnd, End)
        if Scalar is None:
            continue
        try:
            Name = DataValue[Cursor + 4 : TextEnd].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        Parameters[Key].append((Record.offset, Name, Scalar))
    Results = []
    for (Marker, Kind), Items in Parameters.items():
        Family = "Circular" if Kind == "sgCircularPattCntDim" else "Linear"
        Copies = Handles.get((Marker, "moSkDimHandle" + Family + "PattCnt_c"), [])
        if len(Items) != 1 or len(Copies) != 1:
            continue
        Start, Name, Scalar = Items[0]
        Handle, Cursor, End = Copies[0]
        if Scalar + 8 <= Handle:
            Results.append(
                (
                    Markers[Marker][1],
                    Name,
                    Family.lower(),
                    Start,
                    Scalar,
                    Handle,
                    Cursor,
                    End,
                )
            )
    return Results
