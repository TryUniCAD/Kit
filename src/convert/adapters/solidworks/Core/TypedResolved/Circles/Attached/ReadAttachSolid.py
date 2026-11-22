from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)


# the physical carrier is the unique world owned solid with three active faces
def ReadAttachSolid(Nodes: Mapping[int, XmtNode]) -> XmtNode:
    World = RequireXmt(Nodes, 1, 101)
    BodyNode = RequireXmt(Nodes, World.Integer("body"), 12)
    if (
        BodyNode.Integer("owner"),
        BodyNode.Integer("body_type"),
        BodyNode.Integer("next"),
    ) != (1, 1, 0) or sum(
        NodeValue.KindValue == 12 for NodeValue in Nodes.values()
    ) != 1:
        raise ValueError(
            "SOLIDWORKS attached circle requires its one active world solid"
        )
    _ = ReadBodyFaces(Nodes, BodyNode, 3)
    return BodyNode
