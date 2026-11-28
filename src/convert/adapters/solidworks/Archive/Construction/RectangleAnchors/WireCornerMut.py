from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.CornerGraph import (
    CornerGraph,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# publication updates only owned point relation counts and the selected origin persistent mark after validation
def WireCornerMut(
    GraphValue: ProfileGraph,
    OriginValue: OriginGraph,
    AnchorValue: CornerGraph,
    Dimensions: MutableMapping[str, object],
) -> None:
    SketchValue = GraphValue.GeometryValue.SketchValue
    RowsValue = ReadRows(SketchValue.FieldsValue["points"])
    SketchValue.FieldsValue["points"] = (
        *RowsValue,
        {"kind": 1, "point": AnchorValue.ExternalPoint.FieldsValue},
    )
    SketchValue.FieldsValue["npoints"] = len(AnchorValue.PointValues)
    Counters = CastValue(MutableMapping[str, object], SketchValue.FieldsValue["f140"])
    Counters["f08"] = len(AnchorValue.PointValues) + 1
    Dimensions["log_g2"] = ({"d": AnchorValue.RelationValue},)
    Dimensions["nlog2"] = 1
    for PointValue in (AnchorValue.PointValues[0], AnchorValue.ExternalPoint):
        PointValue.FieldsValue["f20"] = FieldInt(PointValue.FieldsValue, "f20") + 1
    OriginValue.PointValue.FieldsValue["f08"] = FieldInt(
        OriginValue.PointValue.FieldsValue, "f0c"
    )
