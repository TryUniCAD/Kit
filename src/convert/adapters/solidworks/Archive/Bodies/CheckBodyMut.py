from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# unknown inherited placeholders must never acquire concrete native class admission by name
def CheckBodyMut(ContextValue: BodyContext, NodeValue: ArchiveNode) -> str:
    ClassValue = NodeValue.ClassValue
    if not isinstance(ClassValue, RuntimeClass):
        raise BodyUnsupported("SOLIDWORKS typed body requires a concrete runtime class")
    Allowed = ContextValue.SchemasValue.get(ClassValue.NameValue, ())
    if ClassValue.SchemaValue not in Allowed:
        ContextValue.UsageValue.MissingNames.add(ClassValue.NameValue)
        raise BodyUnsupported(
            f"unsupported SOLIDWORKS body class {ClassValue.NameValue} schema {ClassValue.SchemaValue}"
        )
    return ClassValue.NameValue
