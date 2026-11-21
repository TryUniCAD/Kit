from convert.adapters.solidworks.Archive.Bodies.ChangeContext import ChangeFlagsMut
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# emitted field order must follow the same concrete native control branches as decoding
def WriteControlMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ContextValue = FrameValue.WriterValue.ContextValue
    if RuleValue.KindValue == "Context":
        ChangeFlagsMut(ContextValue, RuleValue)
    else:
        FlagsValue = ContextValue.FlagsValue
        FlagsValue[RuleValue.NameValue] = (
            FlagsValue.get(RuleValue.NameValue, 0) | RuleValue.MaskValue
        )
        try:
            FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
        finally:
            FlagsValue[RuleValue.NameValue] &= ~RuleValue.MaskValue
