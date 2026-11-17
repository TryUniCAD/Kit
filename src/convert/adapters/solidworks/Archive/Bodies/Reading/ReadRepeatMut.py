from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue


# nonprefix and fixed repetitions need the same inherited field scopes as counted arrays
def ReadRepeatMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    CountValue = (
        RuleValue.MaskValue
        if RuleValue.ModeValue == "Fixed"
        else CastValue(int, ReadScopeValue(FrameValue.ScopeValue, RuleValue.CountValue))
    )
    CountValue = NormalizeCount(
        CountValue, "" if RuleValue.ModeValue == "Fixed" else RuleValue.ModeValue
    )
    ItemsValue: list[dict[str, object]] = []
    for Index in range(CountValue):
        Fields: dict[str, object] = {}
        ChildScope = FieldScope(Fields, FrameValue.ScopeValue, Index)
        FrameValue.FieldsReader(
            ReplaceValue(FrameValue, ScopeValue=ChildScope), RuleValue.BodyValue
        )
        ItemsValue.append(Fields)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = ItemsValue
