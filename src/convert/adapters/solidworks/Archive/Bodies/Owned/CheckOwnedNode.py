from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# direct owners are selected by their field role and cannot also occupy map slots
def CheckOwnedNode(
    NodeValue: ArchiveNode, ClassValue: RuntimeClass, MapValue: ArchiveMaps
) -> None:
    if NodeValue.ClassValue != ClassValue:
        raise ValueError("SOLIDWORKS directly owned node has the wrong concrete class")
    if NodeValue.IndexValue is not None or id(NodeValue) in MapValue.ObjectLookup:
        raise ValueError("SOLIDWORKS directly owned node already owns an archive slot")


# only contexts that declare the concrete schema admit an untagged field
def GetOwnedClass(ContextValue: BodyContext, RuleValue: NativeField) -> RuntimeClass:
    ClassValue = RuntimeClass(RuleValue.TypeValue, 1)
    if ClassValue.SchemaValue not in ContextValue.SchemasValue.get(
        ClassValue.NameValue, ()
    ):
        raise BodyUnsupported(
            f"unsupported SOLIDWORKS native field path {RuleValue.NameValue}"
        )
    return ClassValue
