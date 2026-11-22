from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.CheckPatDatum import (
    CheckPatRule,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatFieldMask import (
    PatFieldMask,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# pattern data owns the contextual selector and its independently typed zero byte validation
def ReadPatField(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    ContextValue = FrameValue.ContextValue
    if RuleValue.KindValue == "Mask":
        with PatFieldMask(ContextValue, RuleValue):
            FrameValue.FieldsReader(FrameValue, RuleValue.BodyValue)
    else:
        CheckPatRule(ContextValue, FrameValue.ScopeValue, RuleValue)
