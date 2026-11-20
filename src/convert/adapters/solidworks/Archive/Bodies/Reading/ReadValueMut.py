from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadBodyTextMut import (
    ReadBodyTextMut,
)
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# shared scalar string and node codecs own wire representation for ordinary body fields
def ReadValueMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Cursor = FrameValue.ReaderValue.Cursor
    Value: object
    if RuleValue.KindValue == "Node":
        Value = ReadNodeMut(FrameValue.ReaderValue)
    elif RuleValue.KindValue == "Text":
        Value = ReadBodyTextMut(Cursor)
    else:
        Value = ReadScalarMut(Cursor, RuleValue.TypeValue)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = Value
