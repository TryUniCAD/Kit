from collections.abc import Mapping
from math import dist as Distance

from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyLoop import (
    ReadBodyLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.JoinChmfEdge import (
    CoordsChmf,
    ReadChmfRoleMap,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    KChmfRoleKey,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.CheckWarmGeo import (
    CheckWarmLines,
    CheckWarmPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.PickWarmEdge import (
    ReadWarmPoint,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheFaces import (
    ReadCacheFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismPlan import PrismPlan
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.Transform import KTransformIdentity


# profile line identities must match every restored stock face and its actual vertex locations
def CheckWarmBase(
    NodesValue: Mapping[int, XmtNode],
    Roles: Mapping[int, KChmfRoleKey],
    PrismValue: PrismPlan,
    LoopValue: LineLoop,
) -> None:
    Expected, _, _, _ = BuildPrism(
        "stock",
        PrismValue.FrameValue,
        PrismValue.LinesValue,
        0.0,
        PrismValue.DepthValue,
    )
    FaceRoles = ReadChmfRoleMap(Expected, PrismValue, LoopValue)
    ExpectedRings = {
        FaceRoles[UseValue.face_id]: tuple(CoordsChmf(Point) for Point in RingValue)
        for UseValue, RingValue in zip(
            Expected.face_uses, ReadMassRings(Expected), strict=True
        )
    }
    if set(Roles.values()) != set(ExpectedRings):
        raise ValueError(
            "saved chamfer restored stock differs from the actual sketch roles"
        )
    for FaceIndex, RoleValue in Roles.items():
        _, FinValues = ReadBodyLoop(NodesValue, NodesValue[FaceIndex])
        Points = tuple(
            tuple(
                Value * 1000.0
                for Value in ReadWarmPoint(
                    NodesValue, NodesValue[Index].Integer("vertex")
                )
            )
            for Index in FinValues
        )
        if len(Points) != 4 or not all(
            sum(Distance(Actual, Point) <= 1e-8 for Actual in Points) == 1
            for Point in ExpectedRings[RoleValue]
        ):
            raise ValueError(
                "saved chamfer restored face differs from its typed stock boundary"
            )


# matched oriented rings may start on a different vertex and must keep all edge directions
def IsSameWarmRing(
    First: tuple[tuple[float, float, float], ...],
    Second: tuple[tuple[float, float, float], ...],
) -> bool:
    return len(First) == len(Second) and any(
        all(
            Distance(Point, Expected) <= 1e-8
            for Point, Expected in zip(
                First, Second[Index:] + Second[:Index], strict=True
            )
        )
        for Index in range(len(First))
    )


# the actual decoded payload is retained only when every outward boundary agrees with its typed construction
def CheckWarmSolid(
    NodesValue: Mapping[int, XmtNode],
    BodyValue: XmtNode,
    Actual: BrepModel,
    PrismValue: PrismPlan,
) -> None:
    (NeutralBody,) = Actual.bodies
    (Region,) = Actual.regions
    if (
        (len(Actual.faces), len(Actual.edges), len(Actual.vertices)) != (7, 15, 10)
        or NeutralBody.transform != KTransformIdentity
        or NeutralBody.region_ids != (Region.id,)
        or NeutralBody.design_body_id
        or NeutralBody.wire_ids
        or NeutralBody.vertex_ids
        or not Region.solid
        or {Value.id: Value.surface_id for Value in Actual.faces}
        != ReadCacheFaces(NodesValue, BodyValue)
    ):
        raise ValueError(
            "saved chamfer B-rep differs from its sole active planar owner"
        )
    Expected, _, _, _ = BuildPrism(
        "bevel",
        PrismValue.FrameValue,
        PrismValue.LinesValue,
        0.0,
        PrismValue.DepthValue,
    )
    RingValues = ReadMassRings(Actual)
    CheckWarmLines(Actual)
    CheckWarmPlanes(Actual, RingValues)
    SourceRings = tuple(
        tuple(CoordsChmf(Point) for Point in RingValue) for RingValue in RingValues
    )
    TargetRings = tuple(
        tuple(CoordsChmf(Point) for Point in RingValue)
        for RingValue in ReadMassRings(Expected)
    )
    Matches = tuple(
        tuple(
            Index
            for Index, Target in enumerate(TargetRings)
            if IsSameWarmRing(RingValue, Target)
        )
        for RingValue in SourceRings
    )
    if (
        len(Matches) != len(TargetRings)
        or any(len(MatchesValue) != 1 for MatchesValue in Matches)
        or len(set(Matches)) != len(Matches)
    ):
        raise ValueError(
            "saved chamfer outward boundary differs from its actual drivers"
        )
