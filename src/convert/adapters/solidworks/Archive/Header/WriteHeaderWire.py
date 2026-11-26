from collections.abc import Mapping
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Header.HeaderFields import (
    KHeaderLayout,
    KHeaderScalars,
    KHeaderWords,
)
from convert.adapters.solidworks.Archive.Header.ReadHeaderBounds import KHeaderBox
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ObjectStore import ObjectStore
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Objects.WriteObjectMut import WriteObjectMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Archive.Strings.EncodeString import EncodeString
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# a typed string supplies its text and encoding while the codec computes its length
def StoreTextMut(Buffer: bytearray, Value: object) -> None:
    if not isinstance(Value, CStringValue):
        raise ValueError("SOLIDWORKS header text requires a typed archive string")
    Buffer.extend(EncodeString(Value, IsSourceFrame=True))


# optional bounds derive their presence and numeric wire values from the model
def StoreBoundsMut(Buffer: bytearray, Value: object) -> None:
    if Value is None:
        Buffer.extend(KHeaderWords["I"].pack(0))
        return
    if not isinstance(Value, tuple):
        raise ValueError("SOLIDWORKS header requires ten bounding box values")
    Numbers = CastValue(tuple[object, ...], Value)
    if len(Numbers) != 10 or not all(
        isinstance(Number, (int, float)) and IsFinite(Number) for Number in Numbers
    ):
        raise ValueError("invalid SOLIDWORKS header bounding box")
    Bounds = CastValue(tuple[float, ...], Numbers)
    if Bounds[9] < 0:
        raise ValueError("invalid SOLIDWORKS header bounding sphere radius")
    Buffer.extend(KHeaderWords["I"].pack(1))
    Buffer.extend(KHeaderBox.pack(*Bounds))


# references need a concrete header owner when allocating the native object map
def StoreChildMut(
    WriterValue: ObjectStore, Value: object, ClassName: str | None = None
) -> None:
    if Value is None:
        WriteObjectMut(WriterValue, None)
        return
    NodeValue = ArchiveNode.RequireNode(Value)
    ClassValue = NodeValue.ClassValue
    if not isinstance(ClassValue, RuntimeClass) or (
        ClassName is not None and ClassValue.NameValue != ClassName
    ):
        raise ValueError("SOLIDWORKS header object has the wrong class")
    WriteObjectMut(WriterValue, NodeValue)


# the writer uses the same ordered field vocabulary and widths as the reader
def StoreFieldsMut(
    Buffer: bytearray,
    WriterValue: ObjectStore,
    LayoutValue: KHeaderLayout,
    Fields: Mapping[str, object],
) -> None:
    for FieldName, WireName in LayoutValue:
        Value = Fields[FieldName]
        ScalarKind = KHeaderScalars.get(WireName)
        if ScalarKind is not None:
            if not isinstance(Value, int) or isinstance(Value, bool):
                raise ValueError(
                    f"SOLIDWORKS header requires an integer for {FieldName}"
                )
            Buffer.extend(EncodeScalar(Value, ScalarKind))
        elif WireName == "text":
            StoreTextMut(Buffer, Value)
        elif WireName == "bounds":
            StoreBoundsMut(Buffer, Value)
        elif WireName == "null":
            if Value is not None:
                raise ValueError("unsupported SOLIDWORKS header configuration object")
            StoreChildMut(WriterValue, None)
        else:
            StoreChildMut(WriterValue, Value, WireName)
