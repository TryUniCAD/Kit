from convert.adapters.solidworks.Core.Native import NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineParamId import (
    LineParamId,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.VectorPlane import PlaneVector


# the public circle preserves actual geometry while exposing only the driving and fixed relations present in the sketch
def CircleSketch(SketchValue: NativeSketch, ParameterIds: set[str]) -> Sketch:
    CircleValue = SketchValue.TypedCircle
    if CircleValue is None:
        raise ValueError("typed circle sketch requires its actual linked circle")
    SketchId = f"sldprt:sketch:{SketchValue.object_id}"
    ArcValue, CenterValue = CircleEntities(SketchId, CircleValue)
    ParamIds: tuple[str, ...] = ()
    Relations: tuple[SketchRelation, ...] = ()
    if CircleValue.DriverName is not None and CircleValue.ModeValue is not None:
        ParamId = LineParamId(SketchValue.object_id, CircleValue.DriverName)
        if ParamId not in ParameterIds:
            raise ValueError(
                "typed circle sketch lacks its projected driving parameter"
            )
        ParamIds = (ParamId,)
        Relations = (
            SketchRelation(
                f"{ArcValue.id}:radial",
                CircleValue.ModeValue,
                (ConstraintRef(ArcValue.id),),
                ParamId,
            ),
            SketchRelation(
                f"{CenterValue.id}:fixed", "fixed", (ConstraintRef(CenterValue.id),)
            ),
        )
    return Sketch(
        SketchId,
        SketchValue.name,
        f"sldprt:plane:{SketchValue.support_plane_id}",
        (ArcValue, CenterValue),
        Relations,
        ParamIds,
        ((ArcValue.id,),),
        provenance=TypedProvenance(CircleValue.OwnerValue, str(SketchValue.object_id)),
        attributes={
            "native_object_id": SketchValue.object_id,
            "support_plane_native_id": SketchValue.support_plane_id,
            "support_plane_source": SketchValue.support_source,
            "unframed_support_plane_native_id": SketchValue.unframed_support_plane_id,
            "native_profile_count": 1,
            "typed_archive_owner": CircleValue.OwnerValue,
        },
    )


# an ordinary circle and its actual local centre retain their separate native sketch array identities
def CircleEntities(
    SketchId: str, CircleValue: LocalCircle
) -> tuple[SketchEntity, SketchEntity]:
    ArcId = f"{SketchId}:circle:{CircleValue.ArcMark}"
    CenterId = f"{SketchId}:point:{CircleValue.CenterMark}"
    Center = PlaneVector(*CircleValue.CenterValue)
    return (
        SketchEntity(
            ArcId,
            GeometryKind.KCircle,
            CircleGeometry(Center, CircleValue.RadiusValue),
            provenance=TypedProvenance(
                CircleValue.OwnerValue, str(CircleValue.ArcMark)
            ),
            attributes={"native_permanent_mark": CircleValue.ArcMark},
        ),
        SketchEntity(
            CenterId,
            GeometryKind.KPoint,
            PointGeometry(Center),
            provenance=TypedProvenance(
                CircleValue.OwnerValue, str(CircleValue.CenterMark)
            ),
            attributes={"native_permanent_mark": CircleValue.CenterMark},
        ),
    )
