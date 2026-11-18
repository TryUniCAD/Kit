from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# unresolved archive placeholders cannot prove the owner of native view state
def NeedViewNode(Value: object, ClassName: str) -> ArchiveNode:
    if (
        not isinstance(Value, ArchiveNode)
        or not isinstance(Value.ClassValue, RuntimeClass)
        or Value.ClassValue != RuntimeClass(ClassName, 1)
    ):
        raise BodyUnsupported(
            "drawing view state requires a concrete current " + ClassName
        )
    return Value
