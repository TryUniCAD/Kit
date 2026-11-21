from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
)


# detached source references must identify the actual parent epoch rather than reuse a plausible synchronized child stamp
def CheckPerpEpoch(
    NodesValue: tuple[ArchiveNode, ...], HeaderValue: ArchiveNode
) -> None:
    for NodeValue in NodesValue:
        if NodeValue.ClassValue.NameValue != "moMatePerpendicular":
            continue
        for RowValue in ReadRows(NodeValue.FieldsValue.get("f3c8")):
            Wrapper = RequireNode(RowValue.get("o"), "moPlaneRef_w")
            if (FieldInt(Wrapper.FieldsValue, "f08") & 0xFFFFFFFF) != FieldInt(
                HeaderValue.FieldsValue, "f40"
            ) or FieldInt(Wrapper.FieldsValue, "f0c") != 0:
                raise ValueError(
                    "perpendicular detached parent epoch or configuration differs"
                )
