from collections.abc import MutableMapping
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Expressions.GetRepeatSize import GetRepeatSize
from convert.adapters.solidworks.Archive.Expressions.ExprFrame import ExprFrame
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# repeated writes follow actual modeled rows while fixed native arities remain enforced
def WriteRepeatMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ItemsValue = ReadBodyRows(FrameValue.ScopeValue, RuleValue.NameValue)
    Expected = GetRepeatSize(
        ExprFrame(
            FrameValue.WriterValue.ContextValue,
            FrameValue.ScopeValue,
            FrameValue.NodeValue,
        ),
        RuleValue,
    )
    if len(ItemsValue) != Expected:
        raise ValueError(
            {
                "Fixed": "native fixed repetition has an incorrect item count",
                "Expression": "native expression repetition differs from its modeled rows",
            }.get(
                RuleValue.ModeValue, "native repeat count differs from its modeled rows"
            )
        )
    for Index, Value in enumerate(ItemsValue):
        if not isinstance(Value, MutableMapping):
            raise ValueError("native repetition requires modeled field mappings")
        ChildScope = FieldScope(
            CastValue(MutableMapping[str, object], Value), FrameValue.ScopeValue, Index
        )
        FrameValue.FieldsWriter(
            ReplaceValue(FrameValue, ScopeValue=ChildScope), RuleValue.BodyValue
        )
