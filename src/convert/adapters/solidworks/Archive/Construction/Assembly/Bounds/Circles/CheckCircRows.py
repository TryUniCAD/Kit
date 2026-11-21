from convert.adapters.solidworks.Archive.Construction.Circles.CircleGraph import (
    CircleGraph,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadRows


# bounds admission must follow the serialized actual point and arc members instead of detached geometry mirrors
def CheckCircRows(Geometry: CircleGraph) -> None:
    FieldsValue = Geometry.SketchValue.FieldsValue
    PointsValue = ReadRows(FieldsValue.get("points"))
    ArcsValue = ReadRows(FieldsValue.get("arcs"))
    if (
        len(PointsValue) != 2
        or len(ArcsValue) != 1
        or PointsValue[0].get("point") is not Geometry.CenterValue.FieldsValue
        or PointsValue[1].get("point") is not Geometry.MarkerValue.FieldsValue
        or ArcsValue[0].get("arc") is not Geometry.ArcValue.FieldsValue
        or FieldsValue.get("lines")
        or FieldsValue.get("nlines") != 0
    ):
        raise ValueError("circle bounds require the actual sole circle array members")
