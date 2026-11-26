from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# native radial lists and face rotations must independently account for the same fins
def CheckVertexFins(
    Nodes: Mapping[int, XmtNode], Vertex: XmtNode, FinValues: set[int]
) -> None:
    HeadValue = Vertex.Integer("halfedge")
    Chain = WalkXmtChain(
        Nodes, HeadValue, 17, "next_at_vx", None, "vertex", Vertex.IndexValue
    )
    if len(Chain) != 3 or set(Chain) != FinValues:
        raise ValueError("attributed active vertex incidence is incomplete")
    IndexValue = HeadValue
    SeenIndices: set[int] = set()
    for _ in Chain:
        FinValue = RequireXmt(Nodes, IndexValue, 17)
        if FinValue.IndexValue not in FinValues or FinValue.IndexValue in SeenIndices:
            raise ValueError("attributed active vertex rotation closes prematurely")
        SeenIndices.add(FinValue.IndexValue)
        IndexValue = Nodes[FinValue.Integer("forward")].Integer("other")
    if IndexValue != HeadValue:
        raise ValueError("attributed active vertex rotation fails to close")
