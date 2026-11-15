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

# the feature record marker precedes the name and the creation action
KFeatureMarker = bytes.fromhex("0a800100")

# the feature record carries this fixed block before its timestamp
KFeatureBlock = bytes.fromhex("0c80000000000000")

# the model reference marker follows the path string
KReferenceMarker = bytes.fromhex("2e80")

# the model reference list declares this fixed count
KReferenceCount = 1


# one feature record keeps the tree name stamp action and id together
@dataclass(frozen=True, slots=True)
class FeatureRecord:
    NameValue: str
    Timestamp: int
    Action: str
    IdValue: int


# the tree tail keeps the last name stamp and count together
@dataclass(frozen=True, slots=True)
class FeatureTail:
    NameValue: str
    Timestamp: int
    Count: int


# one feature tree keeps the records and the tail together
@dataclass(frozen=True, slots=True)
class FeatureTreeData:
    Records: tuple[FeatureRecord, ...]
    Tail: FeatureTail


# one model reference keeps the path name and stamp together
@dataclass(frozen=True, slots=True)
class ModelReference:
    PathValue: str
    NameValue: str
    Marker: int


# the feature tree starts after the header stamp record
def FeatureStart(DataValue: bytes) -> int:
    StampOffset = DataValue.find(b"moStamp_c")
    if StampOffset < 0:
        raise SldprtFormatError("drawing definition has no header stamp")
    Offset = StampOffset + len("moStamp_c") + 10
    Action, Offset = ReadSerialized(DataValue, Offset)
    if Action != "Created":
        raise SldprtFormatError("drawing definition stamp action is invalid")
    return Offset + 4


# the feature tree is a sequence of records followed by one tail record
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


# the model reference follows the feature tree and names the referenced model
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


# the feature tree serializes back to the same record layout
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


# the model reference serializes back to the same list layout
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
