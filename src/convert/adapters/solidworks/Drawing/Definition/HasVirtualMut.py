from collections.abc import Callable
from typing import cast as CastValue

from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleRunner
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape


# virtual serializer choices must use the runtime archive owner
def HasVirtualMut(
    Scope: FieldScope,
    Statement: KRuleShape,
    RunBody: KRuleRunner,
    RunMethod: Callable[[FieldScope, str], None],
) -> bool:
    OwnerName = Scope.OwnerName
    match Statement:
        case ("virtual", MethodRows):
            Methods = dict(CastValue(tuple[tuple[str, str | None], ...], MethodRows))
            if OwnerName not in Methods:
                raise ValueError(f"unqualified drawing virtual owner {OwnerName}")
            MethodName = Methods[OwnerName]
            if MethodName is not None:
                RunMethod(Scope, MethodName)
        case ("if_virtual", OwnerNames, AllowedNames, BodyValue):
            if OwnerName not in CastValue(KRuleShape, OwnerNames):
                raise ValueError(f"unqualified drawing virtual owner {OwnerName}")
            if OwnerName in CastValue(KRuleShape, AllowedNames):
                RunBody(Scope, CastValue(KRuleShape, BodyValue))
        case _:
            return False
    return True
