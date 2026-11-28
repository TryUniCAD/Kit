from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)


# registered cylinder wrapper identities must remain unique without widening the established planar validator
def CheckCylIds(NodeValue: ArchiveNode) -> None:
    Wrappers = tuple(
        RequireNode(Value.get("o"), "moCylinderRef_w")
        for Value in ReadRows(NodeValue.FieldsValue.get("f410"))
    )
    Identities = tuple(FieldInt(Value.FieldsValue, "f78") for Value in Wrappers)
    if len(Identities) != 2 or len(set(Identities)) != 2:
        raise ValueError("concentric registered wrapper identities collide")
