from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyTree import BodyTree
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevLoops import (
    ReadRevLoops,
)


# the rectangular annular revolve must own every active topology record before its source label is considered
def ReadRevolveTree(NodesValue: Mapping[int, XmtNode], IsFull: bool) -> BodyTree:
    BodyIds = WalkXmtChain(
        NodesValue,
        RequireXmt(NodesValue, 1, 101).Integer("body"),
        12,
        OwnerField="owner",
        OwnerValue=1,
    )
    if len(BodyIds) != 1 or set(BodyIds) != {
        NodeValue.IndexValue
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == 12
    }:
        raise ValueError("revolve names require one complete active body")
    BodyValue = NodesValue[BodyIds[0]]
    if BodyValue.Integer("body_type") != 1 or any(
        BodyValue.Integer(NameValue)
        for NameValue in ("child", "ref_instance", "lattice", "mesh", "polyline")
    ):
        raise ValueError("revolve body representation is unqualified")
    FaceIds = ReadBodyFaces(NodesValue, BodyValue, 4 if IsFull else 6)
    LoopIds: set[int] = set()
    FinIds: set[int] = set()
    for IndexValue in FaceIds:
        FaceLoops, FaceFins = ReadRevLoops(NodesValue, NodesValue[IndexValue], IsFull)
        if LoopIds.intersection(FaceLoops) or FinIds.intersection(FaceFins):
            raise ValueError("revolve faces share a trimming owner")
        LoopIds.update(FaceLoops)
        FinIds.update(FaceFins)
    EdgeIds = {NodesValue[IndexValue].Integer("edge") for IndexValue in FinIds}
    VertexIds = {NodesValue[IndexValue].Integer("vertex") for IndexValue in FinIds} - {
        0
    }
    SurfaceIds = {NodesValue[IndexValue].Integer("surface") for IndexValue in FaceIds}
    CurveIds = {
        RequireXmt(NodesValue, IndexValue, 16).Integer("curve")
        for IndexValue in EdgeIds
    }
    PointIds = {
        RequireXmt(NodesValue, IndexValue, 18).Integer("point")
        for IndexValue in VertexIds
    }
    if (
        set(
            WalkXmtChain(
                NodesValue,
                BodyValue.Integer("edge"),
                16,
                OwnerField="owner",
                OwnerValue=BodyValue.IndexValue,
            )
        )
        != EdgeIds
        or set(
            WalkXmtChain(
                NodesValue,
                BodyValue.Integer("vertex"),
                18,
                OwnerField="owner",
                OwnerValue=BodyValue.IndexValue,
            )
        )
        != VertexIds
    ):
        raise ValueError(
            "revolve body edge or vertex chains differ from its complete boundary"
        )
    Inventories = (
        (frozenset((14,)), set(FaceIds), 4 if IsFull else 6),
        (frozenset((15,)), LoopIds, 8 if IsFull else 6),
        (frozenset((17,)), FinIds, 8 if IsFull else 24),
        (frozenset((16,)), EdgeIds, 4 if IsFull else 12),
        (frozenset((18,)), VertexIds, 0 if IsFull else 8),
        (frozenset((50, 51)), SurfaceIds, 4 if IsFull else 6),
        (frozenset((30, 31)), CurveIds, 4 if IsFull else 12),
        (frozenset((29,)), PointIds, 0 if IsFull else 8),
    )
    for KindsValue, Indexes, CountValue in Inventories:
        if len(Indexes) != CountValue or Indexes != {
            NodeValue.IndexValue
            for NodeValue in NodesValue.values()
            if NodeValue.KindValue in KindsValue
        }:
            raise ValueError("revolve does not own the complete active topology")
    if (
        sum(NodeValue.KindValue == 51 for NodeValue in NodesValue.values()) != 2
        or sum(NodeValue.KindValue == 31 for NodeValue in NodesValue.values()) != 4
    ):
        raise ValueError("revolve analytic carriers differ from the witnessed contour")
    return BodyTree(
        BodyValue.IndexValue,
        FaceIds,
        tuple(sorted(LoopIds)),
        tuple(sorted(FinIds)),
        tuple(sorted(EdgeIds)),
        tuple(sorted(VertexIds)),
        tuple(sorted(SurfaceIds)),
        tuple(sorted(CurveIds)),
        tuple(sorted(PointIds)),
    )
