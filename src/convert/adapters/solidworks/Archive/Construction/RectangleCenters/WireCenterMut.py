from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.RectangleCenters.CenterGraph import (
    CenterGraph,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.RequirePolygon import (
    RequirePolygon,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# publication must derive actual endpoint use counts and creation frontiers while preserving the original body contour handles
def WireCenterMut(
    GraphValue: ProfileGraph,
    OriginValue: OriginGraph,
    CenterValue: CenterGraph,
    Dimensions: MutableMapping[str, object],
) -> None:
    Geometry = RequirePolygon(GraphValue.GeometryValue)
    SketchValue = Geometry.SketchValue
    PointRows = ReadRows(SketchValue.FieldsValue["points"])
    LineRows = ReadRows(SketchValue.FieldsValue["lines"])
    SketchValue.FieldsValue["points"] = (
        *PointRows,
        {"kind": 0, "point": CenterValue.CenterValue.FieldsValue},
        {"kind": 1, "point": CenterValue.ExternalPoint.FieldsValue},
    )
    SketchValue.FieldsValue["lines"] = (
        *LineRows,
        *(
            {"flags": 2, "line": LineValue.FieldsValue}
            for LineValue in CenterValue.DiagonalValues
        ),
    )
    SketchValue.FieldsValue.update(
        {
            "npoints": len(CenterValue.PointValues),
            "nlines": len(CenterValue.LineValues),
            "f56c": len(CenterValue.LineValues) + 1,
        }
    )
    Counters = CastValue(MutableMapping[str, object], SketchValue.FieldsValue["f140"])
    Counters.update(
        {
            "f08": len(CenterValue.PointValues) + 1,
            "f0c": len(CenterValue.LineValues) + 1,
        }
    )
    Dimensions.update(
        {
            "nlog2": len(CenterValue.RelationValues),
            "log_g2": tuple({"d": Value} for Value in CenterValue.RelationValues),
        }
    )
    for PointValue in Geometry.PointValues:
        PointValue.FieldsValue["fe8"] = sum(
            PointValue is LineValue.FieldsValue[FieldName]
            for LineValue in CenterValue.LineValues
            for FieldName in ("_start", "_end")
        )
    for Relation in CenterValue.RelationValues:
        for FieldName in ("h1", "h2"):
            HandleValue = ArchiveNode.RequireNode(Relation[FieldName])
            KeyValue = (
                "_point"
                if HandleValue.ClassValue == RuntimeClass("sgPointHandle", 1)
                else "_line"
            )
            EntityValue = ArchiveNode.RequireNode(HandleValue.FieldsValue[KeyValue])
            EntityValue.FieldsValue["f20"] = (
                FieldInt(EntityValue.FieldsValue, "f20") + 1
            )
    OriginValue.PointValue.FieldsValue["f08"] = FieldInt(
        OriginValue.PointValue.FieldsValue, "f0c"
    )
