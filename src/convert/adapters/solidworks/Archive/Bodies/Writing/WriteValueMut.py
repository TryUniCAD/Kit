from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadRuleValue import ReadRuleValue
from convert.adapters.solidworks.Archive.Bodies.RequireHistRef import (
    KHistRefMode,
    RequireHistRef,
)
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.EncodeBodyText import (
    EncodeBodyText,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# body fields emit modeled values through shared codecs instead of retaining serialized operations
def WriteValueMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Value = ReadRuleValue(FrameValue.ScopeValue, RuleValue)
    WriterValue = FrameValue.WriterValue
    if RuleValue.KindValue == "Node":
        if RuleValue.ModeValue == KHistRefMode:
            Value = RequireHistRef(Value)
        WriteNodeMut(WriterValue, Value)
    elif RuleValue.KindValue == "Text":
        WriterValue.OutputValue.extend(EncodeBodyText(Value))
    else:
        WriterValue.OutputValue.extend(EncodeScalar(Value, RuleValue.TypeValue))
