from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.CheckPatDatum import (
    CheckPatRule,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatFieldMask import (
    PatFieldMask,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# pattern data owns the contextual selector and its independently typed zero byte validation
def WritePatField(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ContextValue = FrameValue.WriterValue.ContextValue
    if RuleValue.KindValue == "Mask":
        with PatFieldMask(ContextValue, RuleValue):
            FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
    else:
        CheckPatRule(ContextValue, FrameValue.ScopeValue, RuleValue)
