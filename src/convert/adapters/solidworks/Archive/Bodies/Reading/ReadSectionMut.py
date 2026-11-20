from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Reading.ReadSectSpan import ReadSectSpan


# sized model sections must complete their own bodies before the outer cursor advances
def ReadSectionMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Context = FrameValue.ContextValue
    if Context.VersionValue != KHeaderVersion:
        raise BodyUnsupported("SOLIDWORKS model section requires archive version 19000")
    if Context.FlagsValue.get("conditions", 0) & 0x180000:
        raise BodyUnsupported("unsupported SOLIDWORKS skipped model section")
    Reader = FrameValue.ReaderValue
    Cursor = Reader.Cursor
    Section = ReadSectSpan(Cursor)
    Reader.Cursor = Section
    try:
        FrameValue.FieldsReader(FrameValue, RuleValue.BodyValue)
        if Section.GetRemaining():
            raise ValueError(
                f"SOLIDWORKS model section {RuleValue.MaskValue} has an incorrect length"
            )
    finally:
        Reader.Cursor = Cursor
    Cursor.OffsetValue = Section.GetOffset()
