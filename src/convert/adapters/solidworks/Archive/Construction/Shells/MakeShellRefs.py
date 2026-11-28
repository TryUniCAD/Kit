from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfCarrier,
    MakeChmfFile,
    ReadChmfOwner,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfStockGeom import (
    ChmfFaceRole,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfRefs import (
    MakeChmfEdge,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Archive.Construction.Shells.MakeShellCap import (
    MakeShellCap,
)


# the driving shell has one cut cap and a separate reference for its auxiliary edge
def MakeShellRefs(
    Stock: PartCandidate, AtomValue: ArchiveNode
) -> tuple[ArchiveNode, ArchiveNode]:
    Model = Stock.SystemValue.RootValue
    BossValue = Stock.BossValue.FeatureValue
    OwnerValue = ReadChmfOwner(Stock, BossValue)
    FileValue = MakeChmfFile(Stock)
    Polygon = CastValue(object, Stock.ProfileValue.GeometryValue)
    if not isinstance(Polygon, PolygonGraph) or len(Polygon.LineValues) != 4:
        raise ValueError(
            "shell references require the actual rectangle source segments"
        )
    SegmentIds = tuple(
        FieldInt(Segment.FieldsValue, "f08") for Segment in Polygon.LineValues
    )
    if len(set(SegmentIds)) != 4 or min(SegmentIds) <= 0:
        raise ValueError("shell references require distinct historical segment owners")
    First, Second, Third, Closing = (ChmfFaceRole(False, Value) for Value in SegmentIds)
    CapRoles = (ChmfFaceRole(True, 1), Closing, First, Second, Third)
    EdgeRoles = (Closing, ChmfFaceRole(True, 0), Third, First)
    AtomId = FieldInt(AtomValue.FieldsValue, "f140")
    if AtomId <= 0 or FieldInt(AtomValue.FieldsValue, "f12c") != OwnerValue.Identity:
        raise ValueError("shell references must use the actual consumed stock atom")
    CapValue = MakeShellCap(
        Model,
        AtomId,
        tuple(
            MakeChmfCarrier(RoleValue, OwnerValue, FileValue) for RoleValue in CapRoles
        ),
    )
    EdgeValue, _ = MakeChmfEdge(
        tuple(
            MakeChmfCarrier(RoleValue, OwnerValue, FileValue) for RoleValue in EdgeRoles
        ),
        AtomId,
        Model,
    )
    return CapValue, EdgeValue
