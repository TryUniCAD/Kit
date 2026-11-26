from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadCountMut import (
    ReadCountMut,
)


# repeated records need independent fields while preserving the native inherited scope
def ReadArrayMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    CountValue = ReadCountMut(FrameValue, RuleValue)
    ItemsValue: list[dict[str, object]] = []
    for Index in range(CountValue):
        Fields: dict[str, object] = {}
        ScopeValue = FieldScope(Fields, FrameValue.ScopeValue, Index)
        ChildFrame = ReplaceValue(FrameValue, ScopeValue=ScopeValue)
        FrameValue.FieldsReader(ChildFrame, RuleValue.BodyValue)
        ItemsValue.append(Fields)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = ItemsValue
