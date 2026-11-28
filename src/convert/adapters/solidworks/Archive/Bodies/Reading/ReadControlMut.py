from convert.adapters.solidworks.Archive.Bodies.ChangeContext import ChangeFlagsMut
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# native context changes must keep temporary masked flags scoped to their own fields
def ReadControlMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    ContextValue = FrameValue.ContextValue
    if RuleValue.KindValue == "Context":
        ChangeFlagsMut(ContextValue, RuleValue)
    elif RuleValue.KindValue == "Mask":
        FlagsValue = ContextValue.FlagsValue
        FlagsValue[RuleValue.NameValue] = (
            FlagsValue.get(RuleValue.NameValue, 0) | RuleValue.MaskValue
        )
        try:
            FrameValue.FieldsReader(FrameValue, RuleValue.BodyValue)
        finally:
            FlagsValue[RuleValue.NameValue] &= ~RuleValue.MaskValue
