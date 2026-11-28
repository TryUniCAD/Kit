from math import isclose as IsClose
from struct import Struct as RecordStruct

from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Core.NativeRecords.LinearSketchOwner import KEntityIdentity
from convert.adapters.solidworks.Core.SketchRelations.DimensionFields import (
    RadialAnchor,
    ReadFixedMut,
    ReadLogicQtyMut,
    ReadLogicEndMut,
    ReadRadialMut,
)
from convert.adapters.solidworks.Core.SketchRelations.SketchFields import (
    ClassIndexMut,
    NeedClassMut,
    NeedEntityMut,
    NeedHandleMut,
    NeedOwnerMut,
    NeedWordMut,
    ReadPointMut,
    Require,
)

# ordinary circular segments own two seam references and one distinct center slot
KOrdinaryArc = RecordStruct("<4HdiH4i")


# the origin declares its point class immediately after the sketch and object entries
def CheckOrigin(OriginData: bytes) -> None:
    Cursor = BinaryReader(OriginData)
    NeedOwnerMut(Cursor)
    NeedClassMut(Cursor, "sgSketch")
    NeedWordMut(Cursor, 1, 4)
    Require(ReadPointMut(Cursor, 1) == (0.0, 0.0))
    for _ in range(12):
        NeedWordMut(Cursor, 0, 4)
    NeedWordMut(Cursor, 0)
    ReadLogicQtyMut(Cursor)
    ReadFixedMut(Cursor)
    NeedClassMut(Cursor, "sgPointHandle")
    NeedHandleMut(Cursor, 0)
    ReadLogicEndMut(Cursor)
    NeedClassMut(Cursor, "suObList")


# circle geometry must establish array membership before a relation claims its center
def ReadCircleMut(
    Cursor: BinaryReader,
    Markers: tuple[int, int, int],
    CenterMm: tuple[float, float],
) -> None:
    CenterMark, SeamMark, ArcMark = Markers
    NeedWordMut(Cursor, 2, 4)
    Require(Cursor.OffsetValue + KEntityIdentity.size == CenterMark)
    Position = ReadPointMut(Cursor, 0)
    Require(
        all(
            IsClose(Meters * 1000.0, Value, abs_tol=1e-9)
            for Meters, Value in zip(Position, CenterMm, strict=True)
        )
    )
    Require(Cursor.OffsetValue + KEntityIdentity.size == SeamMark)
    _ = ReadPointMut(Cursor, 2)
    for Expected in (0, 0, 0, 1):
        NeedWordMut(Cursor, Expected, 4)
    Require(Cursor.OffsetValue + KEntityIdentity.size == ArcMark)
    NeedEntityMut(Cursor, 1)
    ArcFields = KOrdinaryArc.unpack(Cursor.TakeBytes(KOrdinaryArc.size))
    Require(ArcFields[:4] == (1, 1, 1, 0))
    Require(ArcFields[5:] == (1, 0, -2, -2, -2, -2))
    for _ in range(8):
        NeedWordMut(Cursor, 0, 4)


# the exact preceding object tag establishes the shared sketch class context
def ReadSketchMut(SketchData: bytes, CountOffset: int) -> BinaryReader:
    TagStart = CountOffset - 2
    if SketchData[CountOffset - 6 : CountOffset - 4] == b"\xff\x7f":
        TagStart = CountOffset - 6
    Require(TagStart >= 6)
    Cursor = BinaryReader(SketchData, TagStart - 6)
    NeedOwnerMut(Cursor)
    return Cursor


# an ordinary circle relation requires the shared point class and its actual center slot
def ReadCenterFix(
    SketchData: bytes,
    OriginData: bytes,
    Markers: tuple[int, int, int],
    CenterMm: tuple[float, float],
    AnchorValue: RadialAnchor,
) -> tuple[int, int] | None:
    CountOffset = Markers[0] - KEntityIdentity.size - 4
    if CountOffset < 6:
        return None
    try:
        CheckOrigin(OriginData)
        Cursor = ReadSketchMut(SketchData, CountOffset)
        PointClassIndex = ClassIndexMut(Cursor) + 2
        Require(Cursor.OffsetValue == CountOffset)
        ReadCircleMut(Cursor, Markers, CenterMm)
        NeedWordMut(Cursor, 1)
        ReadRadialMut(Cursor, AnchorValue, PointClassIndex)
        ReadLogicQtyMut(Cursor)
        Start = Cursor.OffsetValue
        ReadFixedMut(Cursor)
        Require(ClassIndexMut(Cursor) == PointClassIndex)
        NeedHandleMut(Cursor, 0)
        EndValue = Cursor.OffsetValue
        ReadLogicEndMut(Cursor)
        Require(ClassIndexMut(Cursor) == PointClassIndex + 2)
        return (Start, EndValue)
    except ValueError:
        return None
