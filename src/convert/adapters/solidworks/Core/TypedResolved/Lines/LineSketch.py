from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import Sketch

from convert.adapters.solidworks.Core.Native import NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineParamIds import (
    LineParamIds,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineRules import (
    LineRules,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.OriginEntity import (
    OriginEntity,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineEntity import LineEntity
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)


# qualified point owners define line endpoints while actual dimension records supply their complete public relation graph
def LineSketch(SketchValue: NativeSketch, ParameterIds: set[str]) -> Sketch:
    LoopValue = SketchValue.TypedLines
    if LoopValue is None:
        raise ValueError("typed line sketch requires a qualified native ring")
    Entities = tuple(
        LineEntity(SketchValue.object_id, LoopValue, LineValue)
        for LineValue in LoopValue.LinesValue
    )
    OriginValue = (
        None if LoopValue.DimsValue is None else LoopValue.DimsValue.OriginValue
    )
    return Sketch(
        id=f"sldprt:sketch:{SketchValue.object_id}",
        name=SketchValue.name,
        support_plane_id=f"sldprt:plane:{SketchValue.support_plane_id}",
        entities=Entities
        + (
            ()
            if OriginValue is None
            else (OriginEntity(SketchValue.object_id, OriginValue),)
        ),
        constraints=LineRules(
            SketchValue.object_id, LoopValue, tuple(Entity.id for Entity in Entities)
        ),
        parameter_ids=LineParamIds(SketchValue.object_id, LoopValue, ParameterIds),
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
                **(
                    {"typed_line_dimensions": True}
                    if LoopValue.DimsValue is not None
                    else {}
                ),
                "typed_archive_owner": LoopValue.OwnerValue,
                **(
                    {"native_retired_line_rows": LoopValue.RetiredRows}
                    if LoopValue.RetiredRows
                    else {}
                ),
                **(
                    {"native_line_regions": LoopValue.RegionValues}
                    if LoopValue.RegionValues
                    else {}
                ),
                **(
                    {"typed_origin_coincidence": True}
                    if OriginValue is not None
                    else {}
                ),
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
