from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)


# registered wrapper identities must be unique across all mates in the selected configuration
def CheckMateWraps(NodesValue: tuple[ArchiveNode, ...]) -> None:
    WrapperIds = [
        FieldInt(RequireNode(Record.get("o"), "moPlaneRef_w").FieldsValue, "f78")
        for NodeValue in NodesValue
        for Record in ReadRows(NodeValue.FieldsValue.get("f410"))
    ]
    if len(set(WrapperIds)) != len(WrapperIds):
        raise ValueError("typed plane wrapper identities collide across mates")


# the frozen perpendicular readback worker still imports the original wrapper check
CheckMateWrappers = CheckMateWraps
