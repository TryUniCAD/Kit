from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# masked writes restore their archive condition after the selected body
def WriteControlMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    FlagsValue = FrameValue.WriterValue.ContextValue.FlagsValue
    FlagsValue[RuleValue.NameValue] = (
        FlagsValue.get(RuleValue.NameValue, 0) | RuleValue.MaskValue
    )
    try:
        FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
    finally:
        FlagsValue[RuleValue.NameValue] &= ~RuleValue.MaskValue
