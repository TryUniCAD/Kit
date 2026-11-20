from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Expressions.ExprFrame import ExprFrame
from convert.adapters.solidworks.Archive.Expressions.ReadExpression import (
    ReadExpression,
)


# dynamic repetitions must share native expression evaluation with their owning branch guards
def GetRepeatSize(FrameValue: ExprFrame, RuleValue: NativeField) -> int:
    if RuleValue.ModeValue == "Expression":
        CountValue = CastValue(
            int, ReadExpression(FrameValue, RuleValue.ExpressionValue)
        )
        return NormalizeCount(CountValue, "")
    StoredCount = (
        RuleValue.MaskValue
        if RuleValue.ModeValue == "Fixed"
        else ReadScopeValue(FrameValue.ScopeValue, RuleValue.CountValue)
    )
    if type(StoredCount) is not int:
        raise ValueError("native repeat length must be a stored integer")
    return NormalizeCount(
        StoredCount, "" if RuleValue.ModeValue == "Fixed" else RuleValue.ModeValue
    )
