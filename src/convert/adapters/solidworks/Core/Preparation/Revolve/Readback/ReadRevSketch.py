from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdEdge import (
    ReadColdEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import Sketch


# the finite axis uses two distinct native points in the same typed table as the contour
def ReadRevSketch(SketchValue: Sketch, *, IsThin: bool = False) -> Sketch:
    RowsValue = NativeRows(SketchValue.attributes.get("native_point_rows"))
    FrameKey = "typed_thin_revolve_profile" if IsThin else "typed_revolve_profile"
    if (
        SketchValue.attributes.get(FrameKey) is not True
        or len(RowsValue) != (4 if IsThin else 6)
        or len(SketchValue.entities) != (2 if IsThin else 5)
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
            ReadColdEdge(Entity, PointsValue, IsScaled=IsThin)
            for Entity in SketchValue.entities
        ),
        constraints=tuple(
            ReplaceValue(Relation, provenance=None, attributes=FreezeMapping())
            for Relation in SketchValue.constraints
        ),
        provenance=None,
        attributes=FreezeMapping(),
    )
