from convert.adapters.solidworks.Archive.Bodies.ChangeContext import ChangeFlagsMut
from convert.adapters.solidworks.Archive.Bodies.GetVirtualRule import GetVirtualRule
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.IsBranchTaken import IsBranchTaken


# native control flow selects field ownership without synthesizing document values
def ReadControlMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    ContextValue = FrameValue.ContextValue
    if RuleValue.KindValue == "Context":
        ChangeFlagsMut(ContextValue, RuleValue)
    elif RuleValue.KindValue == "Branch":
        IsSelected = IsBranchTaken(
            ContextValue, FrameValue.ScopeValue, FrameValue.NodeValue, RuleValue
        )
        FrameValue.FieldsReader(
            FrameValue, RuleValue.BodyValue if IsSelected else RuleValue.OtherValue
        )
    elif RuleValue.KindValue == "Mask":
        FlagsValue = ContextValue.FlagsValue
        FlagsValue[RuleValue.NameValue] = (
            FlagsValue.get(RuleValue.NameValue, 0) | RuleValue.MaskValue
        )
        try:
            FrameValue.FieldsReader(FrameValue, RuleValue.BodyValue)
        finally:
            FlagsValue[RuleValue.NameValue] &= ~RuleValue.MaskValue
    elif RuleValue.KindValue == "Virtual":
        TargetValue = GetVirtualRule(ContextValue, FrameValue.NodeValue, RuleValue)
        if RuleValue.ModeValue == "Flag":
            if TargetValue:
                FrameValue.FieldsReader(FrameValue, RuleValue.BodyValue)
        elif isinstance(TargetValue, str):
            FrameValue.SchemaReader(FrameValue, TargetValue)
        elif TargetValue is not None:
            raise ValueError("native body dispatch target is not a schema")
