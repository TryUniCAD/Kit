from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.GetRepeatSize import GetRepeatSize
from convert.adapters.solidworks.Archive.Expressions.ExprFrame import ExprFrame
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# nonprefix and fixed repetitions need the same inherited field scopes as counted arrays
def ReadRepeatMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    CountValue = GetRepeatSize(
        ExprFrame(FrameValue.ContextValue, FrameValue.ScopeValue, FrameValue.NodeValue),
        RuleValue,
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
