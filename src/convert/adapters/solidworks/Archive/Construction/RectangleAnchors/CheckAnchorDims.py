from collections import Counter
from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.CheckAnchorRef import (
    CheckAnchorRef,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.DimensionArrays import (
    KDimensionArrays,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonGraph import (
    PolygonGraph,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# anchoring must preserve the already published rectangle constraints and actual entity use counts
def CheckAnchorDims(
    GeometryValue: PolygonGraph, Dimensions: Mapping[str, object]
) -> None:
    CountsValue: Counter[ArchiveNode] = Counter()
    for CountName, FieldName in KDimensionArrays:
        if FieldName not in ("val_g2", "log_g1") and (
            FieldInt(Dimensions, CountName) or ReadRows(Dimensions.get(FieldName))
        ):
            raise ValueError(
                "corner anchor does not admit another dimension or relation group"
            )
    for IndexValue, RowValue in enumerate(ReadRows(Dimensions.get("log_g1"))):
        FieldsValue = RowValue.get("d")
        if not isinstance(FieldsValue, Mapping):
            raise ValueError("corner anchor requires typed unary relation fields")
        FieldsValue = CastValue(Mapping[str, object], FieldsValue)
        HandleValue = ArchiveNode.RequireNode(FieldsValue.get("h1"))
        LineValue = GeometryValue.LineValues[IndexValue]
        if FieldsValue.get("f80") != (4 if IndexValue % 2 == 0 else 5):
            raise ValueError(
                "corner anchor unary relation targets differ from the actual contour"
            )
        CheckAnchorRef(
            HandleValue, LineValue, GeometryValue.SketchValue, IndexValue, False
        )
        CountsValue[LineValue] += 1
    for IndexValue, RowValue in enumerate(ReadRows(Dimensions.get("val_g2"))):
        Dimension = ArchiveNode.RequireNode(RowValue.get("d"))
        if Dimension.ClassValue != RuntimeClass("sgPntPntDist", 1):
            raise ValueError("corner anchor requires actual point distance drivers")
        for OffsetValue, FieldName in enumerate(("h1", "h2")):
            HandleValue = ArchiveNode.RequireNode(Dimension.FieldsValue.get(FieldName))
            PointValue = GeometryValue.PointValues[IndexValue + OffsetValue]
            CheckAnchorRef(
                HandleValue,
                PointValue,
                GeometryValue.SketchValue,
                IndexValue + OffsetValue,
                True,
            )
            CountsValue[PointValue] += 1
    if any(
        FieldInt(EntityValue.FieldsValue, "f20") != CountsValue[EntityValue]
        for EntityValue in (*GeometryValue.PointValues, *GeometryValue.LineValues)
    ):
        raise ValueError(
            "corner anchor requires matching actual entity constraint use counts"
        )
