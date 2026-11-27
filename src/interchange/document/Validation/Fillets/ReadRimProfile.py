from math import isfinite as IsFinite
from typing import Mapping as TypeMap

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.Transform import KTransformIdentity


# a symbolic upper circular rim is valid only for its actual canonical circular profile and frame
def ReadRimProfile(
    Document: CadDocument, Source: FeatureStep, Features: TypeMap[str, FeatureStep]
) -> CircleGeometry:
    Sketch = next(
        (Value for Value in Document.sketches if Value.id == Source.sketch_id), None
    )
    if Sketch is None or Sketch.suppressed or len(Source.input_feature_ids) != 1:
        raise ValueError("radius fillet requires its predecessor circular sketch")
    SketchStep = Features.get(Source.input_feature_ids[0])
    if (
        SketchStep is None
        or SketchStep.kind != FeatureKind.KReference
        or SketchStep.sketch_id != Sketch.id
        or SketchStep.order >= Source.order
        or SketchStep.suppressed
        or SketchStep.definition is not None
    ):
        raise ValueError(
            "radius fillet predecessor must depend on its actual prior sketch feature"
        )
    Plane = next(
        (
            Value
            for Value in Document.support_planes
            if Value.id == Sketch.support_plane_id
        ),
        None,
    )
    if (
        Plane is None
        or Plane.transform != KTransformIdentity
        or Plane.support_selection_id is not None
        or Plane.offset_parameter_id is not None
    ):
        raise ValueError("radius fillet requires its canonical xy sketch frame")
    Circles = tuple(
        Value for Value in Sketch.entities if isinstance(Value.geometry, CircleGeometry)
    )
    if len(Circles) != 1 or any(
        not isinstance(Value.geometry, (CircleGeometry, PointGeometry))
        for Value in Sketch.entities
    ):
        raise ValueError("radius fillet requires one circular predecessor profile")
    Circle = Circles[0]
    Geometry = Circle.geometry
    if not isinstance(Geometry, CircleGeometry):
        raise ValueError("radius fillet circular profile lost its geometry")
    if (
        Circle.kind != GeometryKind.KCircle
        or Circle.construction
        or Sketch.closed_profile_entity_ids != ((Circle.id,),)
        or Geometry.center.x != 0
        or Geometry.center.y != 0
        or type(Geometry.radius) not in (float, int)
        or not IsFinite(Geometry.radius)
        or Geometry.radius <= 0
    ):
        raise ValueError(
            "radius fillet requires one positive origin centered closed circle"
        )
    return Geometry
