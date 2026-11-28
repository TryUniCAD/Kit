from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.PartScopeOwner import HasPartOwner
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadBodyTextMut import (
    ReadBodyTextMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadFrameOwnMut import (
    ReadFrameOwnMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadHistRefMut import (
    ReadHistRefMut,
)
from convert.adapters.solidworks.Archive.Bodies.RequireHistRef import KHistRefMode
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# shared scalar string and node codecs own wire representation for ordinary body fields
def ReadValueMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Cursor = FrameValue.ReaderValue.Cursor
    Value: object
    if RuleValue.KindValue == "Node":
        if HasPartOwner(FrameValue.ContextValue, FrameValue.NodeValue, RuleValue):
            Value = ReadFrameOwnMut(FrameValue)
        elif RuleValue.ModeValue == KHistRefMode:
            Value = ReadHistRefMut(FrameValue)
        else:
            Value = ReadNodeMut(FrameValue.ReaderValue)
    elif RuleValue.KindValue == "Text":
        Value = ReadBodyTextMut(Cursor)
    else:
        Value = ReadScalarMut(Cursor, RuleValue.TypeValue)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = Value
