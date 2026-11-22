from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# an origin anchor must retain the actual rectangular contour and its independent endpoint and row identities
def CheckCornerGeom(GeometryValue: PolygonGraph) -> None:
    SketchValue = GeometryValue.SketchValue
    if (
        len(set(GeometryValue.PointValues)) != 4
        or len(set(GeometryValue.LineValues)) != 4
    ):
        raise ValueError("corner anchor requires distinct contour identities")
    RowsValue = ReadRows(SketchValue.FieldsValue.get("lines"))
    if (
        len(RowsValue) != 4
        or FieldInt(SketchValue.FieldsValue, "nlines") != 4
        or FieldInt(SketchValue.FieldsValue, "npoints") != 4
    ):
        raise ValueError("corner anchor requires complete actual contour counts")
    for IndexValue, (PointValue, LineValue) in enumerate(
        zip(GeometryValue.PointValues, GeometryValue.LineValues, strict=True)
    ):
        if (
            PointValue.ClassValue != RuntimeClass("sgPoint", 1)
            or PointValue.FieldsValue.get("_sketch") is not SketchValue
            or PointValue.FieldsValue.get("ext") is not None
            or LineValue.ClassValue != RuntimeClass("sgLine", 1)
            or LineValue.FieldsValue.get("_sketch") is not SketchValue
            or LineValue.FieldsValue.get("_start") is not PointValue
            or LineValue.FieldsValue.get("_end")
            is not GeometryValue.PointValues[(IndexValue + 1) % 4]
            or LineValue.FieldsValue.get("fc8_s") != IndexValue
            or LineValue.FieldsValue.get("fc8") != IndexValue
            or LineValue.FieldsValue.get("fcc_s") != (IndexValue + 1) % 4
            or LineValue.FieldsValue.get("fcc") != (IndexValue + 1) % 4
            or RowsValue[IndexValue].get("line") is not LineValue.FieldsValue
            or RowsValue[IndexValue].get("flags") != 0
        ):
            raise ValueError(
                "corner anchor contour must retain actual local geometry ownership"
            )
