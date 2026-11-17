from typing import cast as CastValue

from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.ReadOneField import ReadOneField
from convert.adapters.solidworks.Drawing.Definition.ReadRuleExpr import ReadRuleExpr
from convert.adapters.solidworks.Drawing.Definition.ReadRuleRows import ReadRuleRows
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleRunner
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape
from convert.adapters.solidworks.Drawing.Definition.ReadScalarMut import TakeWireInt


# collection framing must retain the separate signed count and expression cases
def HasRepeatMut(
    Scope: FieldScope, Statement: KRuleShape, RunBody: KRuleRunner
) -> bool:
    match Statement:
        case ("repeat", str(FieldName), CountRule, BodyValue):
            CountValue = TakeWireInt(ReadRuleExpr(CountRule, Scope))
        case ("counted", str(FieldName), str(KindName), BodyValue):
            CountValue = max(TakeWireInt(ReadOneField(Scope, KindName)), 0)
        case _:
            return False
    Scope.Fields[FieldName] = ReadRuleRows(
        Scope, CountValue, CastValue(KRuleShape, BodyValue), RunBody
    )
    return True
