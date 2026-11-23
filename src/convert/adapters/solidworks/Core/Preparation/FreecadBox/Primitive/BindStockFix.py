from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginFix import (
    MakeOriginFix,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# the true first corner fixes both planar translation freedoms independently of the two lengths
def BindStockFix(GraphValue: ProfileGraph) -> None:
    Geometry = GraphValue.GeometryValue
    SketchValue = Geometry.SketchValue
    FieldValue = SketchValue.FieldsValue.get("dims")
    if not isinstance(FieldValue, MutableMapping):
        raise ValueError("placed stock requires a local sketch dimension manager")
    Fields = CastValue(MutableMapping[str, object], FieldValue)
    Relations = ReadRows(Fields.get("log_g1"))
    PointValue = Geometry.PointValues[0]
    if (
        len(Relations) != 4
        or Fields.get("nlog1") != 4
        or Fields.get("ng2") != 2
        or PointValue.FieldsValue.get("_sketch") is not SketchValue
        or PointValue.FieldsValue.get("f20") != 1
    ):
        raise ValueError(
            "placed stock needs its actual first rectangle corner and live drivers"
        )
    Fixed = MakeOriginFix(SketchValue, PointValue)
    Fields["log_g1"] = (*Relations, {"d": Fixed.FieldsValue})
    Fields["nlog1"] = len(Relations) + 1
    PointValue.FieldsValue["f20"] = FieldInt(PointValue.FieldsValue, "f20") + 1
