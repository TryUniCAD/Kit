from __future__ import annotations

from dataclasses import dataclass
import struct as Struct

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.core.Native import (
    ClassDecl,
    ReadClass,
    ReadSerialized,
    Serialized,
)

# the marker is needed because the record has no length prefix
KFeatureMarker = bytes.fromhex("0a800100")

# the block is needed because the timestamp is not aligned
KFeatureBlock = bytes.fromhex("0c80000000000000")

# the marker is needed because the name has no length prefix
KReferenceMarker = bytes.fromhex("2e80")

# the count is needed because the list has no terminator
KReferenceCount = 1


# callers need the name stamp action and id as one value
@dataclass(frozen=True, slots=True)
class FeatureRecord:
    NameValue: str
    Timestamp: int
    Action: str
    IdValue: int


# the tail is needed because the last record has no marker
@dataclass(frozen=True, slots=True)
class FeatureTail:
    NameValue: str
    Timestamp: int
    Count: int


# callers need the records and tail as one value
@dataclass(frozen=True, slots=True)
class FeatureTreeData:
    Records: tuple[FeatureRecord, ...]
    Tail: FeatureTail


# callers need the path and name as one value
@dataclass(frozen=True, slots=True)
class ModelReference:
    PathValue: str
    NameValue: str
    Marker: int


# the stamp is needed because the tree has no length prefix
def FeatureStart(DataValue: bytes) -> int:
    StampOffset = DataValue.find(b"moStamp_c")
    if StampOffset < 0:
        raise SldprtFormatError("drawing definition has no header stamp")
    Offset = StampOffset + len("moStamp_c") + 10
    Action, Offset = ReadSerialized(DataValue, Offset)
    if Action != "Created":
        raise SldprtFormatError("drawing definition stamp action is invalid")
    return Offset + 4


# the tail is needed because the last record has no marker
def FeatureTree(DataValue: bytes) -> FeatureTreeData:
    Offset = FeatureStart(DataValue)
    Records: list[FeatureRecord] = []
    while DataValue[Offset : Offset + 3] == b"\xff\xfe\xff":
        NameValue, Offset = ReadSerialized(DataValue, Offset)
        if DataValue[Offset : Offset + 4] != KFeatureMarker:
            Timestamp = Struct.unpack_from("<I", DataValue, Offset)[0]
            Offset += 4
            Count = Struct.unpack_from("<I", DataValue, Offset)[0]
            return FeatureTreeData(
                tuple(Records), FeatureTail(NameValue, Timestamp, Count)
            )
        Offset += 4
        if DataValue[Offset : Offset + 8] != KFeatureBlock:
            raise SldprtFormatError("drawing feature block is invalid")
        Offset += 8
        Timestamp = Struct.unpack_from("<I", DataValue, Offset)[0]
        Offset += 4
        Action, Offset = ReadSerialized(DataValue, Offset)
        IdValue = Struct.unpack_from("<I", DataValue, Offset)[0]
        Offset += 4
        Records.append(FeatureRecord(NameValue, Timestamp, Action, IdValue))
    raise SldprtFormatError("drawing feature tree has no tail record")


# the reference is needed because the view resolves its model by name
def ModelRefAt(DataValue: bytes) -> ModelReference:
    Offset = FeatureStart(DataValue)
    while DataValue[Offset : Offset + 3] == b"\xff\xfe\xff":
        _, Offset = ReadSerialized(DataValue, Offset)
        if DataValue[Offset : Offset + 4] != KFeatureMarker:
            Offset += 8
            break
        Offset += 4 + 8 + 4
        _, Offset = ReadSerialized(DataValue, Offset)
        Offset += 4
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != "moExtObjectList_c":
        raise SldprtFormatError("drawing model reference list is missing")
    (ListCount,) = Struct.unpack_from("<H", DataValue, Offset)
    Offset += 2
    if ListCount != KReferenceCount:
        raise SldprtFormatError("drawing model reference count is invalid")
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != "moExtObject_c":
        raise SldprtFormatError("drawing model reference object is missing")
    ClassName, Offset = ReadClass(DataValue, Offset)
    if ClassName != "moCStringHandle_c":
        raise SldprtFormatError("drawing model reference handle is missing")
    PathValue, Offset = ReadSerialized(DataValue, Offset)
    (Marker,) = Struct.unpack_from("<H", DataValue, Offset)
    if not Marker & 0x8000:
        raise SldprtFormatError("drawing model reference marker is invalid")
    Offset += 2
    NameValue, Offset = ReadSerialized(DataValue, Offset)
    return ModelReference(PathValue, NameValue, Marker)


# the writer needs the exact layout to keep the stream valid
def EncodeTree(TreeData: FeatureTreeData) -> bytes:
    Output = bytearray()
    for Record in TreeData.Records:
        Output.extend(Serialized(Record.NameValue))
        Output.extend(KFeatureMarker)
        Output.extend(KFeatureBlock)
        Output.extend(Struct.pack("<I", Record.Timestamp))
        Output.extend(Serialized(Record.Action))
        Output.extend(Struct.pack("<I", Record.IdValue))
    Output.extend(Serialized(TreeData.Tail.NameValue))
    Output.extend(Struct.pack("<I", TreeData.Tail.Timestamp))
    Output.extend(Struct.pack("<I", TreeData.Tail.Count))
    return bytes(Output)


# the writer needs the exact layout to keep the stream valid
def EncodeModelRef(Reference: ModelReference) -> bytes:
    Output = bytearray()
    Output.extend(ClassDecl("moExtObjectList_c"))
    Output.extend(Struct.pack("<H", KReferenceCount))
    Output.extend(ClassDecl("moExtObject_c"))
    Output.extend(ClassDecl("moCStringHandle_c"))
    Output.extend(Serialized(Reference.PathValue))
    Output.extend(Struct.pack("<H", Reference.Marker))
    Output.extend(Serialized(Reference.NameValue))
    return bytes(Output)
