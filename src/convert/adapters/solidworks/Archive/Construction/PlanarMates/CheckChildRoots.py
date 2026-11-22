from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# child selection admission must retain the proven concrete schemas and current native feature version
def CheckChildRoots(NodesValue: tuple[ArchiveNode, ...]) -> None:
    if any(
        not isinstance(Value.ClassValue, RuntimeClass)
        or Value.ClassValue.SchemaValue != 1
        for Value in NodesValue
    ):
        raise ValueError("mate child construction requires schema one graph roots")
    if FieldInt(NodesValue[-1].FieldsValue, "f2b0") != 19000:
        raise ValueError("mate child datum requires native feature version 19000")
