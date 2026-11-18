from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeLineHandle import (
    MakeLineHandle,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingLine import (
    MakeRingLine,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.MakeRingPoint import (
    MakeRingPoint,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import (
    RequirePolygon,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# selected axis geometry needs its own endpoint and line owners without changing the actual four edge body contour
def AddRevAxisMut(
    GraphValue: ProfileGraph, PlanValue: RevolvePlan
) -> tuple[ProfileGraph, ArchiveNode]:
    Geometry = RequirePolygon(GraphValue.GeometryValue)
    if len(Geometry.PointValues) != 4 or len(Geometry.LineValues) != 4:
        raise ValueError("revolve axis insertion requires its actual four edge profile")
    SketchValue = Geometry.SketchValue
    PointIndex = len(Geometry.PointValues)
    AxisIndex = len(Geometry.LineValues)
    PointValues = (
        *Geometry.PointValues,
        MakeRingPoint(SketchValue, PlanValue.AxisStart, PointIndex),
        MakeRingPoint(SketchValue, PlanValue.AxisEnd, PointIndex + 1),
    )
    AxisValue = MakeRingLine(SketchValue, PointValues, AxisIndex)
    AxisValue.FieldsValue.update(
        {"f54": FieldInt(AxisValue.FieldsValue, "f54") | 8, "fd0": 0}
    )
    LineValues = (*Geometry.LineValues, AxisValue)
    for PointValue in PointValues[PointIndex:]:
        PointValue.FieldsValue.update(
            {
                "h1": MakeLineHandle(SketchValue, AxisValue, AxisIndex),
                "h2": None,
                "fe8": 1,
            }
        )
    FieldsValue = SketchValue.FieldsValue
    FieldsValue.update(
        {
            "points": tuple(
                {"kind": 0, "point": PointValue.FieldsValue}
                for PointValue in PointValues
            ),
            "lines": tuple(
                {
                    "flags": 2 if LineValue is AxisValue else 0,
                    "line": LineValue.FieldsValue,
                }
                for LineValue in LineValues
            ),
            "npoints": len(PointValues),
            "nlines": len(LineValues),
            "f130": len(LineValues) + 1,
            "f56c": len(LineValues) + 1,
        }
    )
    Creation = CastValue(MutableMapping[str, object], FieldsValue["f140"])
    Creation.update({"f08": len(PointValues) + 1, "f0c": len(LineValues) + 1})
    return (
        ProfileGraph(
            GraphValue.ProfileValue,
            PolygonGraph(SketchValue, PointValues, LineValues),
            GraphValue.ReferenceValue,
            GraphValue.FrameValue,
        ),
        AxisValue,
    )
