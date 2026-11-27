from collections.abc import Mapping, Sequence

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.Current.Attributed.CheckVertexFins import (
    CheckVertexFins,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalFins import (
    CheckLocalFins,
)


# each native edge and vertex incidence must agree with the live face boundary
def CheckActiveFins(Nodes: Mapping[int, XmtNode], FinIds: Sequence[int]) -> None:
    ByEdge: dict[int, set[int]] = {}
    ByVertex: dict[int, set[int]] = {}
    for IndexValue in FinIds:
        FinValue = Nodes[IndexValue]
        CheckLocalFins(Nodes, FinValue)
        ByEdge.setdefault(FinValue.Integer("edge"), set()).add(IndexValue)
        ByVertex.setdefault(FinValue.Integer("vertex"), set()).add(IndexValue)
    for IndexValue, FinValues in ByEdge.items():
        EdgeValue = Nodes[IndexValue]
        HeadValue = RequireXmt(Nodes, EdgeValue.Integer("halfedge"), 17)
        if (
            FinValues != {HeadValue.IndexValue, HeadValue.Integer("other")}
            or len(FinValues) != 2
        ):
            raise ValueError("attributed active edge incidence is incomplete")
    for IndexValue, FinValues in ByVertex.items():
        CheckVertexFins(Nodes, Nodes[IndexValue], FinValues)
