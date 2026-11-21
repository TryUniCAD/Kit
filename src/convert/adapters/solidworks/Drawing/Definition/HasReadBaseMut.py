from collections.abc import Callable

from convert.adapters.solidworks.Archive.Reading.ReadTypedNode import ReadTypedMut
from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope
from convert.adapters.solidworks.Drawing.Definition.ClauseTypes import KRuleShape


# inherited fields and inline records retain one archive map across their owners
def HasReadBaseMut(
    Scope: FieldScope,
    Statement: KRuleShape,
    RunMethod: Callable[[FieldScope, str], None],
) -> bool:
    match Statement:
        case ("base", str(MethodName)):
            RunMethod(Scope, MethodName)
        case ("embedded", str(FieldName), str(MethodName)):
            Embedded = Scope.ChildScope()
            RunMethod(Embedded, MethodName)
            Scope.Fields[FieldName] = Embedded.Fields
        case ("inline_header",) if Scope.OwnerName == "moDrawing_c":
            Scope.Fields["fa8"] = ReadTypedMut(Scope.Reader, "moHeader_c")
        case _:
            return False
    return True
