from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleRunner
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape


# repeated classes must make wire progress and retain their native ordering
def ReadRuleRows(
    Scope: FieldScope, CountValue: int, BodyRules: KRuleShape, RunBody: KRuleRunner
) -> tuple[object, ...]:
    Cursor = Scope.Reader.Cursor
    if not 0 <= CountValue <= Cursor.GetRemaining():
        raise ValueError("drawing collection count exceeds the remaining stream")
    Records: list[object] = []
    for _ in range(CountValue):
        Element = Scope.ChildScope()
        StartPosition = Cursor.GetOffset()
        RunBody(Element, BodyRules)
        if StartPosition == Cursor.GetOffset():
            raise ValueError("drawing collection entry consumed no archive bytes")
        Records.append(Element.Fields)
    return tuple(Records)
