from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue


# repeats derive their length from the owning field or a fixed format declaration
def ReadRepeatMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    ModeValue = RuleValue.ModeValue
    LengthValue = (
        RuleValue.MaskValue
        if ModeValue == "Fixed"
        else ReadScopeValue(FrameValue.ScopeValue, RuleValue.CountValue)
    )
    if type(LengthValue) is not int:
        raise ValueError("native repeat length must be a stored integer")
    CountValue = NormalizeCount(LengthValue, "" if ModeValue == "Fixed" else ModeValue)
    ItemsValue: list[dict[str, object]] = []
    for Index in range(CountValue):
        Fields: dict[str, object] = {}
        ChildScope = FieldScope(Fields, FrameValue.ScopeValue, Index)
        FrameValue.FieldsReader(
            ReplaceValue(FrameValue, ScopeValue=ChildScope), RuleValue.BodyValue
        )
        ItemsValue.append(Fields)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = ItemsValue
