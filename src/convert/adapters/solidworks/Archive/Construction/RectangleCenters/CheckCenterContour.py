from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# symmetric coordinates alone cannot admit foreign point rows or a different contour ownership graph
def CheckCenterContour(GeometryValue: PolygonGraph) -> None:
    PointsValue, LinesValue, SketchValue = (
        GeometryValue.PointValues,
        GeometryValue.LineValues,
        GeometryValue.SketchValue,
    )
    if (
        len(PointsValue) != 4
        or len(LinesValue) != 4
        or len(set(PointsValue)) != 4
        or len(set(LinesValue)) != 4
    ):
        raise ValueError(
            "center anchor requires four distinct contour points and lines"
        )
    Positions = tuple(ReadPointPair(Value) for Value in PointsValue)
    LeftValue, BottomValue = Positions[0]
    if (
        not LeftValue < -1e-8
        or not BottomValue < -1e-8
        or Positions
        != (
            (LeftValue, BottomValue),
            (-LeftValue, BottomValue),
            (-LeftValue, -BottomValue),
            (LeftValue, -BottomValue),
        )
    ):
        raise ValueError(
            "center anchor requires an ordered rectangle symmetric about the actual origin"
        )
    PointRows, LineRows = ReadRows(SketchValue.FieldsValue.get("points")), ReadRows(
        SketchValue.FieldsValue.get("lines")
    )
    if (
        len(PointRows) != 4
        or len(LineRows) != 4
        or FieldInt(SketchValue.FieldsValue, "npoints") != 4
        or FieldInt(SketchValue.FieldsValue, "nlines") != 4
    ):
        raise ValueError("center anchor requires complete fresh contour arrays")
    for IndexValue, (PointValue, LineValue) in enumerate(
        zip(PointsValue, LinesValue, strict=True)
    ):
        EndIndex = (IndexValue + 1) % len(PointsValue)
        if (
            PointValue.ClassValue != RuntimeClass("sgPoint", 1)
            or PointValue.FieldsValue.get("_sketch") is not SketchValue
            or PointValue.FieldsValue.get("ext") is not None
            or PointRows[IndexValue].get("kind") != 0
            or PointRows[IndexValue].get("point") is not PointValue.FieldsValue
            or LineValue.ClassValue != RuntimeClass("sgLine", 1)
            or LineValue.FieldsValue.get("_sketch") is not SketchValue
            or LineValue.FieldsValue.get("_start") is not PointValue
            or LineValue.FieldsValue.get("_end") is not PointsValue[EndIndex]
            or any(
                LineValue.FieldsValue.get(NameValue) != SlotValue
                for NameValue, SlotValue in (
                    ("fc8_s", IndexValue),
                    ("fc8", IndexValue),
                    ("fcc_s", EndIndex),
                    ("fcc", EndIndex),
                )
            )
            or LineRows[IndexValue].get("flags") != 0
            or LineRows[IndexValue].get("line") is not LineValue.FieldsValue
        ):
            raise ValueError(
                "center anchor requires actual fresh contour endpoint ownership"
            )
