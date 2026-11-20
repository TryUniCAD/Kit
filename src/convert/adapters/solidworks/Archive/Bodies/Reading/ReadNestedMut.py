from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# embedded values retain a distinct field owner inside the enclosing object
def ReadNestedMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Fields: dict[str, object] = {}
    ScopeValue = FieldScope(Fields, FrameValue.ScopeValue)
    ChildFrame = ReplaceValue(FrameValue, ScopeValue=ScopeValue)
    FrameValue.SchemaReader(ChildFrame, RuleValue.TypeValue)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = Fields
