from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector

from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineSegment import LineSegment
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)


# public lines need permanent native identities while embedded rows retain honest owner level provenance
def LineEntity(
    SketchId: int, LoopValue: LineLoop, LineValue: LineSegment
) -> SketchEntity:
    StartValue, EndValue = (
        LoopValue.PointsValue[LineValue.StartValue],
        LoopValue.PointsValue[LineValue.EndValue],
    )
    NativeId = f"{SketchId}:sgLine:{LineValue.PermanentId}"
    return SketchEntity(
        id=f"sldprt:sketch:{SketchId}:line:{LineValue.PermanentId}",
        kind=GeometryKind.KLine,
        geometry=LineGeometry(
            PlaneVector(*StartValue.PositionValue), PlaneVector(*EndValue.PositionValue)
        ),
        provenance=TypedProvenance(LoopValue.OwnerValue, NativeId),
        attributes=FreezeMapping(
            {
                "native_line_permanent_id": LineValue.PermanentId,
                "native_line_creation_id": LineValue.CreationId,
                "native_point_indices": (LineValue.StartValue, LineValue.EndValue),
                "native_point_creation_ids": (
                    StartValue.CreationId,
                    EndValue.CreationId,
                ),
                "native_fields": LineValue.FieldsValue,
                "typed_archive_owner": {
                    **LoopValue.OwnerValue,
                    "embedded_array": "lines",
                    "row_index": LineValue.IndexValue,
                },
            }
        ),
    )
