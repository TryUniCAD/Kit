from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.PartScopeOwner import (
    PartScopeOwner,
    UsesPartOwner,
)
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
from convert.adapters.solidworks.Archive.Maps.ObjectIndex import ObjectIndex
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# body fields emit modeled values through shared codecs instead of retaining serialized operations
def WriteValueMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Value = ReadRuleValue(FrameValue.ScopeValue, RuleValue)
    WriterValue = FrameValue.WriterValue
    if RuleValue.KindValue == "Node":
        if RuleValue.ModeValue == KHistRefMode:
            Value = RequireHistRef(Value)
        if UsesPartOwner(WriterValue.ContextValue, FrameValue.NodeValue, RuleValue):
            OwnerValue = PartScopeOwner(WriterValue.ContextValue, FrameValue.NodeValue)
            if (
                Value is not OwnerValue
                or ObjectIndex(WriterValue.MapValue, OwnerValue) is None
            ):
                raise ValueError(
                    "SOLIDWORKS component owner differs from its enclosing part"
                )
        WriteNodeMut(WriterValue, Value)
    elif RuleValue.KindValue == "Text":
        WriterValue.OutputValue.extend(EncodeBodyText(Value))
    else:
        WriterValue.OutputValue.extend(EncodeScalar(Value, RuleValue.TypeValue))
