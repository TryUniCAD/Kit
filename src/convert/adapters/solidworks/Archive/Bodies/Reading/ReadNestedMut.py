from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# base records share fields while embedded values retain a distinct native field owner
def ReadNestedMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    if RuleValue.KindValue == "Base":
        FrameValue.SchemaReader(FrameValue, RuleValue.NameValue)
        return
    Fields: dict[str, object] = {}
    ScopeValue = FieldScope(Fields, FrameValue.ScopeValue)
    ChildFrame = ReplaceValue(FrameValue, ScopeValue=ScopeValue)
    FrameValue.SchemaReader(ChildFrame, RuleValue.TypeValue)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = Fields
