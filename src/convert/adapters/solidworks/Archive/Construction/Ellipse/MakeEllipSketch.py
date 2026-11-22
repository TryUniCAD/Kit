from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Ellipse.BindEllipPtsMut import (
    BindEllipPtsMut,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipseGraph import (
    EllipseGraph,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.MakeEllipPoints import (
    KPointRoles,
    MakeEllipPoints,
)
from convert.adapters.solidworks.Archive.Construction.Ellipse.MakeEllipSeg import (
    MakeEllipSeg,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeSketchSeed import (
    MakeSketchSeed,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequireProfile import (
    RequireProfile,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the cold sketch arrays and native creation frontiers derive from the real ellipse and point nodes
def MakeEllipSketch(ProfileValue: ArchiveNode, PlanValue: EllipsePlan) -> EllipseGraph:
    RequireProfile(ProfileValue)
    SketchValue = MakeSketchSeed(ProfileValue)
    PointsValue = MakeEllipPoints(SketchValue, PlanValue)
    SegmentValue = MakeEllipSeg(SketchValue, PointsValue)
    BindEllipPtsMut(SketchValue, SegmentValue, PointsValue)
    PointValues = tuple(PointsValue[RoleName] for RoleName in KPointRoles)
    EllipsesValue = ({"flags": 0, "ellipse": SegmentValue.FieldsValue},)
    FieldsValue = SketchValue.FieldsValue
    FieldsValue.update(
        points=tuple(
            {"kind": 0, "point": PointValue.FieldsValue} for PointValue in PointValues
        ),
        npoints=len(PointValues),
        ellipses=EllipsesValue,
        nellipses=len(EllipsesValue),
        f130=len(EllipsesValue) + 1,
        f56c=len(EllipsesValue) + 1,
    )
    CreationValue = CastValue(dict[str, int], FieldsValue["f140"])
    CreationValue.update(f08=len(PointValues) + 1, f14=len(EllipsesValue) + 1)
    return EllipseGraph(SketchValue, PointValues, SegmentValue)
