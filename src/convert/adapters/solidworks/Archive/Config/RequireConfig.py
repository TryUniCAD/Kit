from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# complete configuration admission excludes drawing headers and unrelated rooted archive objects
def RequireConfig(
    NodeValue: ArchiveNode | None, *, PartRelations: bool = False
) -> ArchiveNode:
    if NodeValue is None or not isinstance(NodeValue.ClassValue, RuntimeClass):
        raise BodyUnsupported(
            "ordinary configuration requires a concrete part or assembly root"
        )
    if NodeValue.ClassValue.SchemaValue != 1 or NodeValue.ClassValue.NameValue not in (
        "moPart_c",
        "moAssembly_c",
    ):
        raise BodyUnsupported(
            "ordinary configuration requires a current part or assembly root"
        )
    if PartRelations and NodeValue.ClassValue.NameValue != "moPart_c":
        raise BodyUnsupported("part equation archive requires a current part root")
    return NodeValue
