from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Header.WriteHeaderWire import (
    StoreChildMut,
    StoreTextMut,
)
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore


# list prefixes derive from their actual immutable item collections
def StoreCountMut(Buffer: bytearray, Value: object) -> tuple[object, ...]:
    if not isinstance(Value, tuple):
        raise ValueError("SOLIDWORKS header requires an ordered tuple of items")
    Items = CastValue(tuple[object, ...], Value)
    Buffer.extend(EncodeCount(len(Items)))
    return Items


# object lists retain the same serialized sequence before any class specific suffix
def StoreObjListMut(
    Buffer: bytearray, WriterValue: ObjectStore, Fields: Mapping[str, object]
) -> None:
    for ItemValue in StoreCountMut(Buffer, Fields["items"]):
        StoreChildMut(WriterValue, ItemValue)


# string lists need the same count grammar while retaining each source text frame
def StoreTextsMut(Buffer: bytearray, Values: object) -> None:
    for Value in StoreCountMut(Buffer, Values):
        StoreTextMut(Buffer, Value)
