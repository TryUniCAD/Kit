from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# dimension handles must retain actual local polygon roles rather than matching unrelated coordinate copies
def CheckRectRoles(GraphValue: ProfileGraph) -> None:
    SketchValue = GraphValue.GeometryValue.SketchValue
    PointValues = GraphValue.GeometryValue.PointValues
    LineValues = GraphValue.GeometryValue.LineValues
    if len(PointValues) != 4 or len(LineValues) != 4:
        raise ValueError("rectangle dimensions require four point and four line roles")
    if len(set(PointValues)) != 4 or len(set(LineValues)) != 4:
        raise ValueError("rectangle geometry requires independently owned entity roles")
    for IndexValue, PointValue in enumerate(PointValues):
        LineValue = LineValues[IndexValue]
        if (
            PointValue.ClassValue != RuntimeClass("sgPoint", 1)
            or LineValue.ClassValue != RuntimeClass("sgLine", 1)
            or PointValue.FieldsValue.get("_sketch") is not SketchValue
            or LineValue.FieldsValue.get("_sketch") is not SketchValue
            or LineValue.FieldsValue.get("_start") is not PointValue
            or LineValue.FieldsValue.get("_end")
            is not PointValues[(IndexValue + 1) % 4]
        ):
            raise ValueError(
                "rectangle dimensions require actual consecutive local endpoint identities"
            )
        if FieldInt(PointValue.FieldsValue, "f20") or FieldInt(
            LineValue.FieldsValue, "f20"
        ):
            raise ValueError(
                "rectangle dimensions require unused point and line constraint references"
            )
