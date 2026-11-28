from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# unknown archive placeholders cannot establish concrete detailing reference ownership
def NeedDetailNode(Value: object, ClassName: str) -> ArchiveNode:
    if (
        not isinstance(Value, ArchiveNode)
        or not isinstance(Value.ClassValue, RuntimeClass)
        or Value.ClassValue != RuntimeClass(ClassName, 1)
    ):
        raise BodyUnsupported(
            "drawing detailing index requires a concrete current " + ClassName
        )
    return Value
