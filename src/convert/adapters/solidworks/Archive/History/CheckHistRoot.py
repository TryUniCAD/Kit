from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# standalone history streams require concrete supported roots and cannot admit an unknown prefix or empty version sequence
def CheckHistRoot(NodeValue: ArchiveNode | None) -> ArchiveNode:
    if (
        NodeValue is None
        or type(NodeValue.ClassValue) is not RuntimeClass
        or NodeValue.ClassValue
        not in (RuntimeClass("moBiography_c", 1), RuntimeClass("moVersionHistory_c", 1))
    ):
        raise BodyUnsupported(
            "ordinary history stream has an unsupported concrete root"
        )
    if (
        NodeValue.ClassValue.NameValue == "moVersionHistory_c"
        and not NodeValue.FieldsValue.get("states")
    ):
        raise BodyUnsupported(
            "ordinary history requires a nonempty current version sequence"
        )
    return NodeValue
