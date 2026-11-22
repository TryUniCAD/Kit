from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# semantic ownership must reject unresolved external placeholders even when their class names match
def RequireNative(NodeValue: object, ClassName: str | None = None) -> ArchiveNode:
    if (
        not isinstance(NodeValue, ArchiveNode)
        or not isinstance(NodeValue.ClassValue, RuntimeClass)
        or NodeValue.ClassValue.SchemaValue != 1
        or ClassName is not None
        and NodeValue.ClassValue.NameValue != ClassName
    ):
        raise ValueError(
            f"typed model expected concrete schema one {ClassName or 'node'}"
        )
    return NodeValue
