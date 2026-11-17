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
    match ExprShape:
        case ("field", str(FieldName), *DefaultValue):
            IsBound, Bound = Scope.FindField(FieldName)
            if IsBound:
                return Bound
            if DefaultValue:
                return ReadRuleExpr(DefaultValue[0], Scope, WireValue)
            raise ValueError(f"missing SOLIDWORKS drawing field {FieldName}")
        case ("conditions",):
            return Scope.Context.Conditions
        case ("class_name",):
            return Scope.OwnerName
        case ("wire",):
            return WireValue
        case ("select", Condition, TrueValue, FalseValue):
            Chosen = (
                TrueValue if ReadRuleExpr(Condition, Scope, WireValue) else FalseValue
            )
            return ReadRuleExpr(Chosen, Scope, WireValue)
        case ("And" | "Or" as JoinType, LeftExpr, RightExpr):
            LeftValue = ReadRuleExpr(LeftExpr, Scope, WireValue)
            return (
                ReadRuleExpr(RightExpr, Scope, WireValue)
                if bool(LeftValue) == (JoinType == "And")
                else LeftValue
            )
        case (str(Operator), *Expressions):
            Operands = tuple(
                ReadRuleExpr(Operand, Scope, WireValue) for Operand in Expressions
            )
            return ReadRuleValue(Operator, Operands)
        case _:
            raise ValueError("invalid SOLIDWORKS drawing expression shape")
