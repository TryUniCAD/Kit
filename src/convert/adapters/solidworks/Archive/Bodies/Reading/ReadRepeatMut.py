from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue


# named repeats use the owning scalar without consuming a second length prefix
def ReadRepeatMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    LengthValue = ReadScopeValue(FrameValue.ScopeValue, RuleValue.CountValue)
    if type(LengthValue) is not int:
        raise ValueError("native repeat length must be a stored integer")
    CountValue = NormalizeCount(LengthValue, RuleValue.ModeValue)
    ItemsValue: list[dict[str, object]] = []
    for Index in range(CountValue):
        Fields: dict[str, object] = {}
        ChildScope = FieldScope(Fields, FrameValue.ScopeValue, Index)
        FrameValue.FieldsReader(
            ReplaceValue(FrameValue, ScopeValue=ChildScope), RuleValue.BodyValue
        )
        ItemsValue.append(Fields)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = ItemsValue
