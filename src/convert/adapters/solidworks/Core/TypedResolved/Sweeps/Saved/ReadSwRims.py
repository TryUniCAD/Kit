from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalFins import (
    CheckLocalFins,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwShell import (
    XmtKindIds,
)


# one rim is the shared spatial boundary of the planar and toroidal face uses
@DataClass(frozen=True, slots=True)
class SwNativeRim:
    CapValue: XmtNode
    PlaneValue: XmtNode
    EdgeValue: XmtNode
    CircleValue: XmtNode
    CapFin: XmtNode
    WallFin: XmtNode


# a native sweep rim is a single vertex free circular use on each participating face
def ReadRimFins(
    NodesValue: Mapping[int, XmtNode], FaceValue: XmtNode
) -> tuple[XmtNode, ...]:
    LoopIds = WalkXmtChain(
        NodesValue,
        FaceValue.Integer("loop"),
        15,
        PreviousField=None,
        OwnerField="face",
        OwnerValue=FaceValue.IndexValue,
    )
    FinsValue = tuple(
        RequireXmt(NodesValue, NodesValue[IndexValue].Integer("halfedge"), 17)
        for IndexValue in LoopIds
    )
    for LoopId, FinValue in zip(LoopIds, FinsValue, strict=True):
        if (
            FinValue.Integer("loop") != LoopId
            or FinValue.Integer("vertex")
            or FinValue.Integer("curve")
            or FinValue.Integer("forward") != FinValue.IndexValue
            or FinValue.Integer("backward") != FinValue.IndexValue
        ):
            raise ValueError("SOLIDWORKS saved sweep has a foreign periodic fin")
        CheckLocalFins(NodesValue, FinValue)
    return FinsValue


# carrier and topology references must resolve through the associated edge and mate
def ReadSwRim(
    NodesValue: Mapping[int, XmtNode],
    BodyValue: XmtNode,
    CapValue: XmtNode,
    WallFins: tuple[XmtNode, ...],
) -> SwNativeRim:
    PlaneValue = RequireXmt(NodesValue, CapValue.Integer("surface"), 50)
    (CapFin,) = ReadRimFins(NodesValue, CapValue)
    WallFin = RequireXmt(NodesValue, CapFin.Integer("other"), 17)
    EdgeValue = RequireXmt(NodesValue, CapFin.Integer("edge"), 16)
    CircleValue = RequireXmt(NodesValue, EdgeValue.Integer("curve"), 31)
    if (
        WallFin not in WallFins
        or PlaneValue.Integer("owner") != CapValue.IndexValue
        or EdgeValue.Integer("owner") != BodyValue.IndexValue
        or EdgeValue.Integer("halfedge") not in (CapFin.IndexValue, WallFin.IndexValue)
        or CircleValue.Integer("owner") != EdgeValue.IndexValue
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep rim has a foreign trim or carrier owner"
        )
    return SwNativeRim(CapValue, PlaneValue, EdgeValue, CircleValue, CapFin, WallFin)


# exactly two reciprocal owned rings bound the measured saved wall and both caps
def ReadSwRims(
    NodesValue: Mapping[int, XmtNode],
    BodyValue: XmtNode,
    FacesValue: tuple[XmtNode, ...],
) -> tuple[XmtNode, SwNativeRim, SwNativeRim]:
    (TorusId,) = XmtKindIds(NodesValue, 54)
    TorusValue = NodesValue[TorusId]
    (WallValue,) = (
        FaceValue for FaceValue in FacesValue if FaceValue.Integer("surface") == TorusId
    )
    if (
        TorusValue.Integer("owner") != WallValue.IndexValue
        or WallValue.String("sense") != "+"
    ):
        raise ValueError("SOLIDWORKS saved sweep torus is foreign to its wall face")
    WallFins = ReadRimFins(NodesValue, WallValue)
    FirstRim, SecondRim = tuple(
        ReadSwRim(NodesValue, BodyValue, CapValue, WallFins)
        for CapValue in FacesValue
        if CapValue is not WallValue
    )
    CheckRimLists(NodesValue, BodyValue, WallFins, FirstRim, SecondRim)
    CheckSwSurfs(NodesValue, BodyValue)
    return TorusValue, FirstRim, SecondRim


# complete rim lists keep otherwise reachable alternate trims outside this projection
def CheckRimLists(
    NodesValue: Mapping[int, XmtNode],
    BodyValue: XmtNode,
    WallFins: tuple[XmtNode, ...],
    FirstRim: SwNativeRim,
    SecondRim: SwNativeRim,
) -> None:
    RimValues = (FirstRim, SecondRim)
    EdgesValue = WalkXmtChain(NodesValue, BodyValue.Integer("edge"), 16)
    CurvesValue = WalkXmtChain(NodesValue, BodyValue.Integer("boundary_curve"), 31)
    FinIds = {
        Value.IndexValue
        for RimValue in RimValues
        for Value in (RimValue.CapFin, RimValue.WallFin)
    }
    if (
        len(WallFins) != 2
        or len(FinIds) != 4
        or FinIds != XmtKindIds(NodesValue, 17)
        or {NodesValue[IndexValue].Integer("loop") for IndexValue in FinIds}
        != XmtKindIds(NodesValue, 15)
        or len(EdgesValue) != 2
        or set(EdgesValue) != XmtKindIds(NodesValue, 16)
        or {RimValue.EdgeValue.IndexValue for RimValue in RimValues} != set(EdgesValue)
        or len(CurvesValue) != 2
        or set(CurvesValue) != XmtKindIds(NodesValue, 31)
        or {RimValue.CircleValue.IndexValue for RimValue in RimValues}
        != set(CurvesValue)
        or {RimValue.PlaneValue.IndexValue for RimValue in RimValues}
        != XmtKindIds(NodesValue, 50)
    ):
        raise ValueError("SOLIDWORKS saved sweep has another resident boundary")


# the body surface chain must retain the exact owned analytic boundary inventory
def CheckSwSurfs(NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode) -> None:
    SeenValue: set[int] = set()
    IndexValue, Previous = BodyValue.Integer("boundary_surface"), 0
    while IndexValue:
        NodeValue = NodesValue[IndexValue]
        if (
            IndexValue in SeenValue
            or NodeValue.KindValue not in (50, 54)
            or NodeValue.Integer("previous") != Previous
        ):
            raise ValueError("SOLIDWORKS saved sweep surface chain is not reciprocal")
        SeenValue.add(IndexValue)
        Previous, IndexValue = IndexValue, NodeValue.Integer("next")
    if SeenValue != XmtKindIds(NodesValue, 50) | XmtKindIds(NodesValue, 54):
        raise ValueError("SOLIDWORKS saved sweep surface chain has a foreign owner")
