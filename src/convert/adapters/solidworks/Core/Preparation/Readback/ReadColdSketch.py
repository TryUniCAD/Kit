from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdEdge import (
    ReadColdEdge,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import Sketch


# the explicit native point table restores each emitted line without rounding its wire value
def ReadColdSketch(Original: Sketch) -> Sketch:
    if Original.attributes.get("typed_line_loop") is not True:
        raise ValueError("SOLIDWORKS cold sketch requires a typed line loop")
    RowsValue = NativeRows(Original.attributes.get("native_point_rows"))
    if not 3 <= len(RowsValue) == len(Original.entities) <= 64 or any(
        RowValue.get("array_index") != Index for Index, RowValue in enumerate(RowsValue)
    ):
        raise ValueError("SOLIDWORKS cold sketch point rows disagree with its lines")
    Coordinates = tuple(
        NativeRecord(NativeRecord(RowValue.get("native_fields")).get("pos"))
        for RowValue in RowsValue
    )
    return ReplaceValue(
        Original,
        entities=tuple(
            ReadColdEdge(Entity, Coordinates) for Entity in Original.entities
        ),
        attributes=FreezeMapping(),
        provenance=None,
    )
