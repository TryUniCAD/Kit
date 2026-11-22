from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfCarrier,
    MakeChmfFile,
    MakeChmfNode,
    ReadChmfOwner,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfStockGeom import (
    ChmfFaceRole,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfRefs import (
    MakeChmfEdge,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import (
    MakeSelfComp,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# the removed boundary pairs its end carrier with all four historical sketch sides
def MakeShellCap(
    Model: ArchiveNode, AtomId: int, Carriers: tuple[ArchiveNode, ...]
) -> ArchiveNode:
    References = [{"f08": Value} for Value in (*Carriers, None)]
    FaceValue = MakeChmfNode(
        "moFaceRef_c",
        {
            "f60": 1,
            "f64": 0,
            "f08": len(References),
            "fe8": 768,
            "f70": 0,
            "f28": 1e100,
            "f30": 1e100,
            "f40": None,
            "f10": References,
            "f48": 0,
            "nd0": 0,
            "fd0": [],
            "fec": 19000,
            "has_f18": 0,
            "nf0": 0,
            "ff0": [],
        },
    )
    Fields = CompRefFields(MakeSelfComp(Model))
    Fields.update(f18=AtomId, f1c=AtomId, has_alias=0, fe8=FaceValue, ff0=None)
    return MakeChmfNode("moCompFace_c", Fields)


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
