from __future__ import annotations

from typing import TYPE_CHECKING

from convert.adapters.solidworks.Container.Format import (
    SERIALIZED_STRING_MARKER as SerializedStringMarker,
    dimension_scalar_value_offset as DimensionScalarValue,
)

if TYPE_CHECKING:
    from convert.adapters.solidworks.Core.Native import NativeClass


# count parameter names must be bounded by their typed record before pairing with a handle
def ReadCountParam(
    DataValue: bytes,
    Record: NativeClass,
    Cursor: int,
    EndOffset: int,
    Nested: NativeClass | None,
) -> tuple[int, str, int] | None:
    if Record.name not in (
        "sgCircularPattCntDim",
        "sgLinearPattCntDim",
    ) or DataValue[
        Cursor : Cursor + 4
    ] != bytes(4):
        return None
    Cursor += 4
    if Nested and Nested.offset == Cursor and Nested.name == "moIntegerParameter_c":
        Cursor += 6 + len(Nested.name)
    elif (
        Cursor + 2 <= EndOffset
        and 0x8000 <= int.from_bytes(DataValue[Cursor : Cursor + 2], "little") < 0xFFFF
    ):
        Cursor += 2
    else:
        return None
    if (
        Cursor + 6 > EndOffset
        or not int.from_bytes(DataValue[Cursor : Cursor + 2], "little") & 0x8000
    ):
        return None
    Cursor += 2
    if DataValue[Cursor : Cursor + 3] != SerializedStringMarker:
        return None
    TextSize = DataValue[Cursor + 3]
    if not 0 < TextSize < 255:
        return None
    TextEnd = Cursor + 4 + 2 * TextSize
    Scalar = DimensionScalarValue(DataValue, TextEnd, EndOffset)
    if Scalar is None:
        return None
    try:
        ParamName = DataValue[Cursor + 4 : TextEnd].decode("utf-16le")
    except UnicodeDecodeError:
        return None
    return Record.offset, ParamName, Scalar
