from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Revolves.ReadRevLoops import (
    ReadRevLoops,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylRims import (
    CheckCylChain,
)


# the distinct wall inventory selects the closed annular branch of the periodic reader
def HasAnnularWalls(NodesValue: Mapping[int, XmtNode]) -> bool:
    return sum(Value.KindValue == 51 for Value in NodesValue.values()) == 2


# every face must exhaust its two attached periodic rings without substituting another owner
def ReadAnnFins(NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode) -> set[int]:
    SurfaceValues: list[XmtNode] = []
    LoopIds: set[int] = set()
    FinIds: set[int] = set()
    for FaceId in ReadBodyFaces(NodesValue, BodyValue, 4):
        FaceValue = NodesValue[FaceId]
        Surface = NodesValue[FaceValue.Integer("surface")]
        Loops, FinsValue = ReadRevLoops(NodesValue, FaceValue, True)
        if (
            Surface.KindValue not in (50, 51)
            or Surface.Integer("owner") != FaceId
            or Surface.String("sense") != "+"
            or FaceValue.String("sense") not in ("+", "-")
            or LoopIds.intersection(Loops)
            or FinIds.intersection(FinsValue)
        ):
            raise ValueError("local annulus has foreign cap or wall ownership")
        LoopIds.update(Loops)
        FinIds.update(FinsValue)
        SurfaceValues.append(Surface)
    CheckCylChain(BodyValue.Integer("boundary_surface"), tuple(SurfaceValues))
    return FinIds


# the circular carrier chain must follow four actual edges and own their positive fins
def CheckAnnGraph(NodesValue: Mapping[int, XmtNode], BodyValue: XmtNode) -> None:
    FinIds = ReadAnnFins(NodesValue, BodyValue)
    EdgeIds = WalkXmtChain(
        NodesValue,
        BodyValue.Integer("edge"),
        16,
        OwnerField="owner",
        OwnerValue=BodyValue.IndexValue,
    )
    if len(EdgeIds) != 4 or len(FinIds) != 8:
        raise ValueError("local annulus requires four owned edges and eight fins")
    CurveValues: list[XmtNode] = []
    AllFins: set[int] = set()
    for IndexValue in EdgeIds:
        EdgeValue = NodesValue[IndexValue]
        FinValue = RequireXmt(NodesValue, EdgeValue.Integer("halfedge"), 17)
        Circle = RequireXmt(NodesValue, EdgeValue.Integer("curve"), 31)
        if (
            FinValue.Integer("edge") != IndexValue
            or FinValue.String("sense") != "+"
            or Circle.Integer("owner") != IndexValue
            or Circle.String("sense") != "+"
        ):
            raise ValueError(
                "local annulus has foreign edge or circular carrier ownership"
            )
        AllFins.update((FinValue.IndexValue, FinValue.Integer("other")))
        CurveValues.append(Circle)
    if AllFins != FinIds:
        raise ValueError("local annulus edges do not own all periodic fins")
    CheckCylChain(BodyValue.Integer("boundary_curve"), tuple(CurveValues))
