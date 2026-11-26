from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import Sketch

from convert.adapters.solidworks.Core.Native import NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineEntity import LineEntity
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)


# qualified point owners define line endpoints rather than additional public sketch entities or invented constraints
def LineSketch(SketchValue: NativeSketch) -> Sketch:
    LoopValue = SketchValue.TypedLines
    if LoopValue is None:
        raise ValueError("typed line sketch requires a qualified native ring")
    Entities = tuple(
        LineEntity(SketchValue.object_id, LoopValue, LineValue)
        for LineValue in LoopValue.LinesValue
    )
    return Sketch(
        id=f"sldprt:sketch:{SketchValue.object_id}",
        name=SketchValue.name,
        support_plane_id=f"sldprt:plane:{SketchValue.support_plane_id}",
        entities=Entities,
        closed_profile_entity_ids=(
            tuple(Entities[Index].id for Index in LoopValue.OrderValue),
        ),
        provenance=TypedProvenance(LoopValue.OwnerValue, str(SketchValue.object_id)),
        attributes=FreezeMapping(
            {
                "native_object_id": SketchValue.object_id,
                "native_marker_count": len(SketchValue.markers),
                "native_profile_count": 1,
                "support_plane_native_id": SketchValue.support_plane_id,
                "support_plane_source": SketchValue.support_source,
                "unframed_support_plane_native_id": SketchValue.unframed_support_plane_id,
                "typed_line_loop": True,
                "typed_archive_owner": LoopValue.OwnerValue,
                "native_point_rows": tuple(
                    {
                        "array_index": Point.IndexValue,
                        "native_creation_id": Point.CreationId,
                        "native_fields": Point.FieldsValue,
                        "line_handles": tuple(
                            {
                                "class": Handle.ClassValue.NameValue,
                                "object_index": Handle.IndexValue,
                                "fields": dict(Handle.FieldsValue),
                            }
                            for Handle in Point.HandlesValue
                        ),
                    }
                    for Point in LoopValue.PointsValue
                ),
            }
        ),
    )
