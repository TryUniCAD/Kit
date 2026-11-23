from convert.adapters.solidworks.Archive.Motion.MotionStudy import MotionStudy
from convert.adapters.solidworks.Archive.Motion.ReadMotionBody import ReadMotionBody
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.ReadNativeCount import ReadCountMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# the saved caption index must join its actual inactive study and end at the physical stream boundary
def ReadMotionStudy(BufferValue: bytes) -> MotionStudy:
    CursorValue = BinaryReader(BufferValue)
    StudyValue = ReadMotionBody(CursorValue)
    CountStart = CursorValue.GetOffset()
    CountValue = ReadCountMut(CursorValue, 1)
    if (
        CountValue != 1
        or BufferValue[CountStart : CursorValue.GetOffset()] != EncodeCount(CountValue)
        or ReadCStringMut(CursorValue) != CStringValue(StudyValue.NameValue, True)
        or CursorValue.GetRemaining()
    ):
        raise ValueError("assembly motion has an unqualified caption directory")
    return StudyValue
