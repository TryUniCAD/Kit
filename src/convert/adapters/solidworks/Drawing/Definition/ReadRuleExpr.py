from typing import cast as CastValue

from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.ReadRuleValue import ReadRuleValue
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape


# expression operands resolve in the current archive field and condition scope
def ReadRuleExpr(
    Expression: object, Scope: FieldScope, WireValue: int | float | None = None
) -> object:
    if not isinstance(Expression, tuple):
        return Expression
    ExprShape = CastValue(KRuleShape, Expression)
    if not ExprShape or not isinstance(ExprShape[0], str):
        raise ValueError("invalid SOLIDWORKS drawing expression shape")
    Operator, ExprCount = ExprShape[0], len(ExprShape)
    if Operator == "field" and ExprCount > 1 and isinstance(ExprShape[1], str):
        FieldName = ExprShape[1]
        IsBound, Bound = Scope.FindField(FieldName)
        if IsBound:
            return Bound
        if ExprCount > 2:
            return ReadRuleExpr(ExprShape[2], Scope, WireValue)
        raise ValueError(f"missing SOLIDWORKS drawing field {FieldName}")
    if ExprCount == 1:
        if Operator == "conditions":
            return Scope.Context.Conditions
        if Operator == "class_name":
            return Scope.OwnerName
        if Operator == "wire":
            return WireValue
    if Operator == "select" and ExprCount == 4:
        Chosen = (
            ExprShape[2]
            if ReadRuleExpr(ExprShape[1], Scope, WireValue)
            else ExprShape[3]
        )
        return ReadRuleExpr(Chosen, Scope, WireValue)
    if Operator in ("And", "Or") and ExprCount == 3:
        LeftValue = ReadRuleExpr(ExprShape[1], Scope, WireValue)
        return (
            ReadRuleExpr(ExprShape[2], Scope, WireValue)
            if bool(LeftValue) == (Operator == "And")
            else LeftValue
        )
    Operands = tuple(
        ReadRuleExpr(Operand, Scope, WireValue) for Operand in ExprShape[1:]
    )
    return ReadRuleValue(Operator, Operands)
