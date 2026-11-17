from dataclasses import dataclass as DataClass
from math import isclose as IsClose, isfinite as IsFinite
from struct import Struct as RecordStruct

from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadTextMut
from convert.adapters.solidworks.Core.SketchRelations.SketchFields import (
    ClassIndexMut,
    NeedClassMut,
    NeedHandleMut,
    NeedNullMut,
    NeedWordMut,
    Require,
)

# the dimension value is a native double before its alternate value flag
KLengthValue = RecordStruct("<d")

# ordinary value constraints end with scalar state and direction values
KValueTail = RecordStruct("<ii3d")


# the already bound radial value provides an independent cursor check
@DataClass(frozen=True, slots=True)
class RadialAnchor:
    NameValue: str
    OffsetValue: int
    ValueMm: float


# only the ordinary named length parameter can anchor this value dimension
def ReadLengthMut(Cursor: BinaryReader, AnchorValue: RadialAnchor) -> int:
    ParameterClassIndex = ClassIndexMut(Cursor)
    Require(ClassIndexMut(Cursor) < ParameterClassIndex)
    Require(ReadTextMut(Cursor) == AnchorValue.NameValue)
    _ = Cursor.TakeBytes(16)
    _ = ReadTextMut(Cursor)
    NeedNullMut(Cursor)
    Require(Cursor.OffsetValue == AnchorValue.OffsetValue)
    (ValueInMetres,) = KLengthValue.unpack(Cursor.TakeBytes(KLengthValue.size))
    Require(IsFinite(ValueInMetres))
    Require(IsClose(ValueInMetres * 1000.0, AnchorValue.ValueMm, abs_tol=1e-9))
    NeedWordMut(Cursor, 0, 1)
    return ParameterClassIndex


# the ordinary dimension suffix has no tolerance attachment or alternate name
def ReadDimTailMut(Cursor: BinaryReader) -> None:
    NeedNullMut(Cursor)
    _ = Cursor.TakeBytes(16)
    NeedNullMut(Cursor)
    _ = Cursor.ReadUnsigned(2)
    NeedWordMut(Cursor, 0, 1)


# the radius consumes its own two handles before any logical relation is read
def ReadRadialMut(
    Cursor: BinaryReader, AnchorValue: RadialAnchor, PointClassIndex: int
) -> None:
    NeedClassMut(Cursor, "sgCircleDim")
    _ = Cursor.TakeBytes(4)
    ParameterClassIndex = ReadLengthMut(Cursor, AnchorValue)
    ReadDimTailMut(Cursor)
    NeedWordMut(Cursor, 3, 4)
    _ = Cursor.TakeBytes(6)
    NeedWordMut(Cursor, 0)
    Require(ClassIndexMut(Cursor) > max(PointClassIndex, ParameterClassIndex))
    NeedHandleMut(Cursor, 0)
    NeedClassMut(Cursor, "sgEntHandle")
    NeedHandleMut(Cursor, -2)
    TailValues = KValueTail.unpack(Cursor.TakeBytes(KValueTail.size))
    Require(all(IsFinite(Value) for Value in TailValues[2:]))


# the logical relation type lives on its own dimension base and has no parameter
def ReadFixedMut(Cursor: BinaryReader) -> None:
    _ = Cursor.TakeBytes(4)
    NeedNullMut(Cursor)
    ReadDimTailMut(Cursor)
    NeedWordMut(Cursor, 0x11, 4)
    for Expected in (2, 0, 0, 0xFFFE, 0):
        NeedWordMut(Cursor, Expected)


# only one logical record follows the other proven empty dimension arrays
def ReadLogicQtyMut(Cursor: BinaryReader) -> None:
    for Expected in (0, 0, 0, 1):
        NeedWordMut(Cursor, Expected)


# other relation and pattern lists must end before the display list object
def ReadLogicEndMut(Cursor: BinaryReader) -> None:
    for _ in range(7):
        NeedWordMut(Cursor, 0)
