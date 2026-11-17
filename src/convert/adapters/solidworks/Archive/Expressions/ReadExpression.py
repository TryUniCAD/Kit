from functools import partial as PartialValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Expressions.ExprCollection import (
    ExprCollection,
)
from convert.adapters.solidworks.Archive.Expressions.ExprCompare import IsExprCompared
from convert.adapters.solidworks.Archive.Expressions.ExprFrame import ExprFrame
from convert.adapters.solidworks.Archive.Expressions.ExprLogic import ExprLogic
from convert.adapters.solidworks.Archive.Expressions.ExprLookup import ExprLookup
from convert.adapters.solidworks.Archive.Expressions.ExprMath import ExprMath
from convert.adapters.solidworks.Archive.Expressions.ExprSpecial import ExprSpecial


# field expressions are a closed pure vocabulary compiled from documented native source rules
def ReadExpression(FrameValue: ExprFrame, Expression: tuple[object, ...]) -> object:
    ActionValue, Arguments = CastValue(str, Expression[0]), Expression[1:]
    ReadValue = PartialValue(ReadExpression, FrameValue)
    if ActionValue == "literal":
        return Arguments[0]
    if ActionValue in ("scope", "context", "node", "class_name"):
        return {
            "scope": FrameValue.ScopeValue,
            "context": FrameValue.ContextValue.FlagsValue,
            "node": FrameValue.NodeValue,
            "class_name": FrameValue.NodeValue.ClassValue.NameValue,
        }[ActionValue]
    if ActionValue in ("lookup", "lookup_or"):
        return ExprLookup(Arguments, ReadValue, ActionValue == "lookup_or")
    if ActionValue in ("select", "And", "Or"):
        return ExprLogic(ActionValue, Arguments, ReadValue)
    if ActionValue == "compare":
        return IsExprCompared(Arguments, ReadValue)
    if ActionValue in ("sequence", "mapping"):
        return ExprCollection(ActionValue, Arguments, ReadValue)
    if ActionValue in ("is_node", "class_of", "virtual", "sum_field"):
        return ExprSpecial(FrameValue, ActionValue, Arguments, ReadValue)
    return ExprMath(
        ActionValue,
        tuple(ReadValue(CastValue(tuple[object, ...], Child)) for Child in Arguments),
    )
