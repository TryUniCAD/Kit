from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeText import ReadCStringMut


# shared scalar string and node codecs own wire representation for ordinary body fields
def ReadValueMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Cursor = FrameValue.ReaderValue.Cursor
    Value: object
    if RuleValue.KindValue == "Node":
        Value = ReadNodeMut(FrameValue.ReaderValue)
    elif RuleValue.KindValue == "Text":
        TextValue = ReadCStringMut(Cursor)
        Value = (
            TextValue.TextValue if TextValue.IsUnicode else ("A", TextValue.TextValue)
        )
    else:
        Value = ReadScalarMut(Cursor, RuleValue.TypeValue)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = Value
