from convert.adapters.solidworks.Archive.Bodies.ChangeContext import ChangeFlagsMut
from convert.adapters.solidworks.Archive.Bodies.GetVirtualRule import GetVirtualRule
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.IsBranchTaken import IsBranchTaken
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# emitted field order must follow the same concrete native control branches as decoding
def WriteControlMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ContextValue = FrameValue.WriterValue.ContextValue
    if RuleValue.KindValue == "Context":
        ChangeFlagsMut(ContextValue, RuleValue)
    elif RuleValue.KindValue == "Branch":
        IsSelected = IsBranchTaken(
            ContextValue, FrameValue.ScopeValue, FrameValue.NodeValue, RuleValue
        )
        FrameValue.FieldsWriter(
            FrameValue, RuleValue.BodyValue if IsSelected else RuleValue.OtherValue
        )
    elif RuleValue.KindValue == "Mask":
        FlagsValue = ContextValue.FlagsValue
        FlagsValue[RuleValue.NameValue] = (
            FlagsValue.get(RuleValue.NameValue, 0) | RuleValue.MaskValue
        )
        try:
            FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
        finally:
            FlagsValue[RuleValue.NameValue] &= ~RuleValue.MaskValue
    elif RuleValue.KindValue == "Virtual":
        TargetValue = GetVirtualRule(ContextValue, FrameValue.NodeValue, RuleValue)
        if RuleValue.ModeValue == "Flag":
            if TargetValue:
                FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
        elif isinstance(TargetValue, str):
            FrameValue.SchemaWriter(FrameValue, TargetValue)
        elif TargetValue is not None:
            raise ValueError("native body dispatch target is not a schema")
