from dataclasses import replace as ReplaceValue

from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import PointGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch
from interchange.geometry.Models.VectorPlane import PlaneVector


# a contour starting at zero does not carry the design intent of an actively anchored corner
def ReadCornerAnchor(SketchValue: Sketch) -> Sketch:
    if (
        len(SketchValue.closed_profile_entity_ids) != 1
        or len(SketchValue.closed_profile_entity_ids[0]) != 4
        or len(SketchValue.entities) != 5
        or len({Entity.id for Entity in SketchValue.entities}) != 5
    ):
        raise ValueError("anchored rectangle requires four contour lines and one datum")
    (ContourIds,) = SketchValue.closed_profile_entity_ids
    (OriginValue,) = (
        Entity for Entity in SketchValue.entities if Entity.id not in ContourIds
    )
    if (
        OriginValue.kind != GeometryKind.KPoint
        or type(OriginValue.geometry) is not PointGeometry
        or OriginValue.geometry.point != PlaneVector(0.0, 0.0)
        or not OriginValue.construction
        or not OriginValue.fixed
        or OriginValue.attributes
    ):
        raise ValueError("anchored rectangle requires an explicit fixed origin datum")
    DatumRef = ConstraintRef(OriginValue.id)
    Anchors = tuple(
        Relation
        for Relation in SketchValue.constraints
        if any(RefValue.entity_id == OriginValue.id for RefValue in Relation.references)
    )
    if len(Anchors) != 1:
        raise ValueError("anchored rectangle requires one active origin coincidence")
    (AnchorValue,) = Anchors
    StartRef = ConstraintRef(ContourIds[0], "start")
    EndRef = ConstraintRef(ContourIds[-1], "end")
    if (
        AnchorValue.kind != "coincident"
        or not AnchorValue.driving
        or AnchorValue.suppressed
        or AnchorValue.parameter_id is not None
        or AnchorValue.attributes
        or AnchorValue.references
        not in (
            (DatumRef, StartRef),
            (StartRef, DatumRef),
            (DatumRef, EndRef),
            (EndRef, DatumRef),
        )
        or any(Relation.provenance is not None for Relation in SketchValue.constraints)
    ):
        raise ValueError("rectangle anchor must select the actual starting corner")
    return ReplaceValue(
        SketchValue,
        entities=tuple(
            Entity for Entity in SketchValue.entities if Entity is not OriginValue
        ),
        constraints=tuple(
            Relation
            for Relation in SketchValue.constraints
            if Relation is not AnchorValue
        ),
    )
