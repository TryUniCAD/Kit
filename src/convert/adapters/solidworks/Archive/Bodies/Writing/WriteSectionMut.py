from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion

from convert.adapters.solidworks.Archive.Bodies.Fields.SectionField import (
    KSectSkipMask,
    KSectLength,
)


# a refused section must leave the surrounding archive bytes untouched
def WriteSectionMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Writer = FrameValue.WriterValue
    Context = Writer.ContextValue
    if Context.VersionValue != KHeaderVersion:
        raise BodyUnsupported("SOLIDWORKS model section requires archive version 19000")
    if Context.FlagsValue.get("conditions", 0) & KSectSkipMask:
        raise BodyUnsupported("unsupported SOLIDWORKS skipped model section")
    Outer = Writer.OutputValue
    Section = bytearray()
    Writer.OutputValue = Section
    try:
        FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
    finally:
        Writer.OutputValue = Outer
    Outer.extend(KSectLength.pack(len(Section)))
    Outer.extend(Section)
