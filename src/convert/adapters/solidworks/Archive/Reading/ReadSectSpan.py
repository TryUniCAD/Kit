from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader

from convert.adapters.solidworks.Archive.Bodies.Fields.SectionField import (
    KSectLength,
)


# a child section needs an absolute end without moving the parent cursor
def ReadSectSpan(Cursor: BinaryReader) -> BinaryReader:
    Section = BinaryReader(Cursor.BytesValue, Cursor.OffsetValue, Cursor.LimitValue)
    ByteCount = int(KSectLength.unpack(Section.TakeBytes(KSectLength.size))[0])
    if ByteCount > Section.GetRemaining():
        raise ValueError("SOLIDWORKS model section exceeds its remaining stream")
    Section.LimitValue = Section.GetOffset() + ByteCount
    return Section
