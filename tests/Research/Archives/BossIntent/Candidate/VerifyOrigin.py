from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import PointGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch


# the origin anchor needs its own native owner even when it shares a corner position
def VerifyOrigin(
    SketchValue: Sketch,
    TargetSketch: Sketch,
    Timeline: tuple[FeatureStep, ...],
    FirstEdge: str,
) -> str:
    (Origin,) = [Entity for Entity in SketchValue.entities if Entity.fixed]
    (TargetOrigin,) = [Entity for Entity in TargetSketch.entities if Entity.fixed]
    assert (
        Origin.construction
        and TargetOrigin.construction
        and TargetOrigin.id == Origin.id
    )
    assert (
        isinstance(Origin.geometry, PointGeometry)
        and TargetOrigin.geometry == Origin.geometry
    )
    assert (Origin.geometry.point.x, Origin.geometry.point.y) == (0.0, 0.0)
    (OriginFeature,) = [
        StepValue for StepValue in Timeline if StepValue.name == "Origin"
    ]
    assert OriginFeature.provenance is not None
    assert OriginFeature.provenance.native_id == str(
        Origin.attributes["native_origin_feature_id"]
    )
    (Anchor,) = [
        RuleValue
        for RuleValue in SketchValue.constraints
        if RuleValue.kind == "coincident" and RuleValue.provenance is not None
    ]
    assert Anchor.references == (
        ConstraintRef(Origin.id),
        ConstraintRef(FirstEdge, "start"),
    )
    return Origin.id
