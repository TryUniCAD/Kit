from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import (
    PickCylFace,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyTree import BodyTree
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevLoops import (
    ReadRevLoops,
)


# implicit cylinder names need the sole solid owned by the active world
def CheckCylOwner(NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode) -> None:
    BodyIndex = BodyValue.IndexValue
    if (
        WalkXmtChain(
            NodesValue,
            RequireXmt(NodesValue, 1, 101).Integer("body"),
            12,
            OwnerField="owner",
            OwnerValue=1,
        )
        != (BodyIndex,)
        or BodyValue.Integer("body_type") != 1
        or any(
            BodyValue.Integer(NameValue)
            for NameValue in (
                "child",
                "ref_instance",
                "lattice",
                "mesh",
                "polyline",
                "vertex",
            )
        )
    ):
        raise ValueError("implicit cylinder has an unqualified body owner")


# the two circular carriers must own the selected edges and their actual trim fins
def ReadCylEdges(
    NodesValue: Mapping[int, XmtNode], EdgeIds: tuple[int, ...], FinIds: set[int]
) -> set[int]:
    CurveIds: set[int] = set()
    for EdgeIndex in EdgeIds:
        EdgeValue = NodesValue[EdgeIndex]
        CurveValue = RequireXmt(NodesValue, EdgeValue.Integer("curve"), 31)
        FinIndex = EdgeValue.Integer("halfedge")
        if (
            FinIndex not in FinIds
            or NodesValue[FinIndex].Integer("edge") != EdgeIndex
            or CurveValue.Integer("owner") != EdgeIndex
            or CurveValue.IndexValue in CurveIds
        ):
            raise ValueError(
                "implicit cylinder has foreign edge or circular curve owners"
            )
        CurveIds.add(CurveValue.IndexValue)
    return CurveIds


# implicit cylinder names need both actual circular trims and the complete owned solid boundary
def ReadCylBodyTree(NodesValue: Mapping[int, XmtNode]) -> BodyTree:
    Lateral, _, BodyValue = PickCylFace(NodesValue)
    CheckCylOwner(NodesValue, BodyValue)
    BodyIndex = BodyValue.IndexValue
    FaceIds = ReadBodyFaces(NodesValue, BodyValue, 3)
    EdgeIds = WalkXmtChain(
        NodesValue,
        BodyValue.Integer("edge"),
        16,
        OwnerField="owner",
        OwnerValue=BodyIndex,
    )
    if len(EdgeIds) != 2:
        raise ValueError("implicit cylinder requires its two owned circular edges")
    LoopIds: set[int] = set()
    FinIds: set[int] = set()
    SurfaceIds: set[int] = set()
    for FaceIndex in FaceIds:
        FaceValue = NodesValue[FaceIndex]
        IsLateral = FaceValue is Lateral
        SurfaceValue = RequireXmt(
            NodesValue, FaceValue.Integer("surface"), 51 if IsLateral else 50
        )
        Loops, FaceFins = ReadRevLoops(
            NodesValue, FaceValue, True, FullLoopCount=2 if IsLateral else 1
        )
        FinEdges = {NodesValue[IndexValue].Integer("edge") for IndexValue in FaceFins}
        if (
            SurfaceValue.Integer("owner") != FaceIndex
            or LoopIds.intersection(Loops)
            or FinIds.intersection(FaceFins)
            or not FinEdges.issubset(EdgeIds)
            or (IsLateral and FinEdges != set(EdgeIds))
        ):
            raise ValueError("implicit cylinder has foreign trimming or surface owners")
        LoopIds.update(Loops)
        FinIds.update(FaceFins)
        SurfaceIds.add(SurfaceValue.IndexValue)
    CurveIds = ReadCylEdges(NodesValue, EdgeIds, FinIds)
    Inventories: tuple[tuple[tuple[int, ...], set[int]], ...] = (
        ((15,), LoopIds),
        ((16,), set(EdgeIds)),
        ((17,), FinIds),
        ((18, 29), set()),
        ((30, 31), CurveIds),
        ((50, 51), SurfaceIds),
    )
    if any(
        Actual
        != {
            NodeValue.IndexValue
            for NodeValue in NodesValue.values()
            if NodeValue.KindValue in KindsValue
        }
        for KindsValue, Actual in Inventories
    ):
        raise ValueError("implicit cylinder has incomplete active topology ownership")
    return BodyTree(
        BodyIndex,
        FaceIds,
        tuple(sorted(LoopIds)),
        tuple(sorted(FinIds)),
        EdgeIds,
        (),
        tuple(sorted(SurfaceIds)),
        tuple(sorted(CurveIds)),
        (),
    )
