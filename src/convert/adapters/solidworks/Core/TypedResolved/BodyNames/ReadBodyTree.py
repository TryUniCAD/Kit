from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyTree import BodyTree
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyLoop import (
    ReadBodyLoop,
)


# complete native topology must be proved before any document body receives its source label
def ReadBodyTree(NodesValue: Mapping[int, XmtNode]) -> BodyTree:
    WorldValue = RequireXmt(NodesValue, 1, 101)
    BodyIds = WalkXmtChain(
        NodesValue, WorldValue.Integer("body"), 12, OwnerField="owner", OwnerValue=1
    )
    if len(BodyIds) != 1 or set(BodyIds) != {
        NodeValue.IndexValue
        for NodeValue in NodesValue.values()
        if NodeValue.KindValue == 12
    }:
        raise ValueError("native names require one unambiguous active body")
    BodyValue = NodesValue[BodyIds[0]]
    if BodyValue.Integer("body_type") != 1 or any(
        BodyValue.Integer(NameValue)
        for NameValue in ("child", "ref_instance", "lattice", "mesh", "polyline")
    ):
        raise ValueError("native body representation is outside the witnessed profile")
    FaceIds = ReadBodyFaces(NodesValue, BodyValue)
    LoopIds: set[int] = set()
    FinIds: set[int] = set()
    for IndexValue in FaceIds:
        LoopIndex, FaceFins = ReadBodyLoop(NodesValue, NodesValue[IndexValue])
        if LoopIndex in LoopIds or FinIds.intersection(FaceFins):
            raise ValueError("native faces share a trimming owner")
        LoopIds.add(LoopIndex)
        FinIds.update(FaceFins)
    EdgeIds = {NodesValue[IndexValue].Integer("edge") for IndexValue in FinIds}
    VertexIds = {NodesValue[IndexValue].Integer("vertex") for IndexValue in FinIds}
    SurfaceIds = {NodesValue[IndexValue].Integer("surface") for IndexValue in FaceIds}
    CurveIds = {
        RequireXmt(NodesValue, IndexValue, 16).Integer("curve")
        for IndexValue in EdgeIds
    }
    PointIds = {
        RequireXmt(NodesValue, IndexValue, 18).Integer("point")
        for IndexValue in VertexIds
    }
    Inventories = (
        (14, set(FaceIds), 6),
        (15, LoopIds, 6),
        (17, FinIds, 24),
        (16, EdgeIds, 12),
        (18, VertexIds, 8),
        (50, SurfaceIds, 6),
        (30, CurveIds, 12),
        (29, PointIds, 8),
    )
    for KindValue, Indexes, CountValue in Inventories:
        if len(Indexes) != CountValue or Indexes != {
            NodeValue.IndexValue
            for NodeValue in NodesValue.values()
            if NodeValue.KindValue == KindValue
        }:
            raise ValueError("native body does not own the complete active topology")
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
