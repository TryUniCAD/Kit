from math import isfinite as IsFinite
from struct import Struct as RecordStruct

from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import (
    ReadTagMut,
    ReadTypeDescMut,
)
from convert.adapters.solidworks.Core.LinearSketchOwner import (
    KEntityIdentity,
    KOrdinaryEntity,
)

# ordinary point rows store two dimensional positions before their type and usage
KPointHead = RecordStruct("<HddHH")

# compact local handles carry signed block and external identities
KPointHandleContext = RecordStruct("<ii")


# structural gates keep unsupported shapes from yielding a partial interpretation
def Require(CheckValue: bool) -> None:
    if not CheckValue:
        raise ValueError("unsupported SOLIDWORKS sketch relation layout")


# counted arrays must have the expected shape before the next field is read
def NeedWordMut(Cursor: BinaryReader, Expected: int, Width: int = 2) -> None:
    Require(Cursor.ReadUnsigned(Width) == Expected)


# null archive objects consume tags without allocating any map entries
def NeedNullMut(Cursor: BinaryReader) -> None:
    Require(ReadTagMut(Cursor).KindValue == "Null")


# the original profile must own its sketch instead of borrowing previous geometry
def NeedOwnerMut(Cursor: BinaryReader) -> None:
    NeedNullMut(Cursor)
    NeedWordMut(Cursor, 0, 4)


# fresh declarations identify the exact class before ownership is inferred
def NeedClassMut(Cursor: BinaryReader, ClassName: str) -> None:
    Require(ReadTagMut(Cursor).KindValue == "NewClass")
    Require(ReadTypeDescMut(Cursor) == RuntimeClass(ClassName, 1))


# class references remain separate from aliases of existing objects
def ClassIndexMut(Cursor: BinaryReader) -> int:
    TagValue = ReadTagMut(Cursor)
    if TagValue.KindValue != "ClassRef" or TagValue.IndexValue is None:
        raise ValueError("SOLIDWORKS sketch relation requires a class reference")
    return TagValue.IndexValue


# local handles must prove identity in the owning sketch instead of a block or model
def NeedHandleMut(Cursor: BinaryReader, SlotValue: int) -> None:
    Index = Cursor.ReadUnsigned(2)
    if Index == 0x777F:
        Index = int.from_bytes(Cursor.TakeBytes(4), "little", signed=True)
    Require(Index == SlotValue)
    Require(KPointHandleContext.unpack(Cursor.TakeBytes(8)) == (-1, 0))


# optional objects must be absent before an ordinary entity row has fixed width
def NeedEntityMut(Cursor: BinaryReader, OwnerIndex: int) -> None:
    Flags, OwnerValue, CreationId = KEntityIdentity.unpack(
        Cursor.TakeBytes(KEntityIdentity.size)
    )
    Require(Flags == 0 and OwnerValue == OwnerIndex and CreationId > 0)
    VisibilityAndEntity = Cursor.TakeBytes(KOrdinaryEntity.size)
    Require(KOrdinaryEntity.unpack(VisibilityAndEntity) == (0, 0, 4, 0, 0, 0))


# point roles distinguish the sketch origin and circle center from an endpoint
def ReadPointMut(Cursor: BinaryReader, RoleValue: int) -> tuple[float, float]:
    NeedEntityMut(Cursor, 0)
    Flags, XValue, YValue, RoleCode, UsesValue = KPointHead.unpack(
        Cursor.TakeBytes(KPointHead.size)
    )
    ExpectedFlags = 0x1F if RoleValue == 1 else 0x1E
    ExpectedUses = {0: 1, 1: 0, 2: 2}[RoleValue]
    Require((Flags, RoleCode, UsesValue) == (ExpectedFlags, RoleValue, ExpectedUses))
    Require(IsFinite(XValue) and IsFinite(YValue))
    if RoleValue == 2:
        NeedClassMut(Cursor, "sgArcHandle")
        NeedHandleMut(Cursor, 0)
    else:
        NeedNullMut(Cursor)
    NeedNullMut(Cursor)
    NeedWordMut(Cursor, int(RoleValue == 0))
    NeedWordMut(Cursor, 0xFFFFFFFE, 4)
    _ = Cursor.TakeBytes(32)
    NeedWordMut(Cursor, 0)
    _ = Cursor.ReadUnsigned(2)
    return (XValue, YValue)
