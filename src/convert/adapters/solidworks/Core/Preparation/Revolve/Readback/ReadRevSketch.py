from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdEdge import (
    ReadColdEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import Sketch


# the finite axis uses two distinct native points in the same typed table as the contour
def ReadRevSketch(SketchValue: Sketch) -> Sketch:
    RowsValue = NativeRows(SketchValue.attributes.get("native_point_rows"))
    if (
        SketchValue.attributes.get("typed_revolve_profile") is not True
        or len(RowsValue) != 6
        or len(SketchValue.entities) != 5
        or any(
            RowValue.get("array_index") != IndexValue
            for IndexValue, RowValue in enumerate(RowsValue)
        )
    ):
        raise ValueError("SOLIDWORKS revolve readback lacks its typed profile points")
    PointsValue = tuple(
        NativeRecord(NativeRecord(RowValue.get("native_fields")).get("pos"))
        for RowValue in RowsValue
    )
    return ReplaceValue(
        SketchValue,
        entities=tuple(
            ReadColdEdge(Entity, PointsValue) for Entity in SketchValue.entities
        ),
        constraints=tuple(
            ReplaceValue(Relation, provenance=None, attributes=FreezeMapping())
            for Relation in SketchValue.constraints
        ),
        provenance=None,
        attributes=FreezeMapping(),
    )
