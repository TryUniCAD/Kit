from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.EncodeBodyText import (
    EncodeBodyText,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# body fields emit modeled values through shared codecs instead of retaining serialized operations
def WriteValueMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Value = ReadScopeValue(FrameValue.ScopeValue, RuleValue.NameValue)
    WriterValue = FrameValue.WriterValue
    if RuleValue.KindValue == "Node":
        WriteNodeMut(WriterValue, Value)
    elif RuleValue.KindValue == "Text":
        WriterValue.OutputValue.extend(EncodeBodyText(Value))
    else:
        WriterValue.OutputValue.extend(EncodeScalar(Value, RuleValue.TypeValue))
