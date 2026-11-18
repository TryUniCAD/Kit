from convert.adapters.solidworks.Archive.Construction.Origin.OriginGraph import (
    OriginGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# component origin selection must refer to the same fresh model origin and its actual local point
def RequireOrigin(GraphValue: ProfileGraph, OriginValue: OriginGraph) -> None:
    if type(OriginValue) is not OriginGraph:
        raise TypeError("corner anchor requires its constructed origin graph")
    ProfileValue, SketchValue, PointValue = (
        OriginValue.ProfileValue,
        OriginValue.SketchValue,
        OriginValue.PointValue,
    )
    if (
        ProfileValue.ClassValue != RuntimeClass("moOriginProfileFeature_c", 1)
        or ProfileValue.FieldsValue.get("owner")
        is not GraphValue.ProfileValue.FieldsValue.get("owner")
        or ProfileValue.FieldsValue.get("pd_f80") is not SketchValue
        or ProfileValue.FieldsValue.get("pd_ff0")
        != GraphValue.ProfileValue.FieldsValue.get("pd_ff0")
    ):
        raise ValueError(
            "corner anchor requires the actual matching front origin owner"
        )
    RowsValue = ReadRows(SketchValue.FieldsValue.get("points"))
    if (
        len(RowsValue) != 1
        or RowsValue[0].get("point") is not PointValue.FieldsValue
        or PointValue.FieldsValue.get("_sketch") is not SketchValue
        or FieldInt(PointValue.FieldsValue, "f0c") != 1
        or FieldInt(PointValue.FieldsValue, "f08") not in (0, 1)
        or ReadPointPair(PointValue) != (0.0, 0.0)
    ):
        raise ValueError("corner anchor requires the origin first actual local point")
    if (
        FieldInt(ProfileValue.FieldsValue, "f08") < 0
        or ProfileValue.FieldsValue.get("f3dc") != 0
        or ProfileValue.FieldsValue.get("pd_f110") is not None
    ):
        raise ValueError("corner anchor requires a registered ordinary fresh origin")
    HandleValue = ArchiveNode.RequireNode(OriginValue.Constraint.FieldsValue.get("h1"))
    if (
        OriginValue.Constraint.FieldsValue.get("f80") != 17
        or HandleValue.FieldsValue.get("_point") is not PointValue
    ):
        raise ValueError("origin must retain its own actual fixed point constraint")
