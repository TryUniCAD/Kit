from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.VectorPlane import PlaneVector


# the box contour must bind its authored lengths to editable perpendicular edges on the actual support
def MakeBoxProfile(
    SketchId: str,
    SketchName: str,
    PlaneId: str,
    LengthValue: float,
    WidthValue: float,
    ParameterIds: tuple[str, str],
    *,
    NegativeV: bool = False,
) -> Sketch:
    LocalWidth = -WidthValue if NegativeV else WidthValue
    Corners = (
        PlaneVector(0.0, 0.0),
        PlaneVector(LengthValue, 0.0),
        PlaneVector(LengthValue, LocalWidth),
        PlaneVector(0.0, LocalWidth),
    )
    Entities = tuple(
        SketchEntity(f"edge/{Index}", GeometryKind.KLine, LineGeometry(Start, End))
        for Index, (Start, End) in enumerate(
            zip(Corners, (*Corners[1:], Corners[0]), strict=True)
        )
    )
    AxisRelations = tuple(
        SketchRelation(
            f"relation/axis/{Index}",
            "horizontal" if Index % 2 == 0 else "vertical",
            (ConstraintRef(Entity.id),),
        )
        for Index, Entity in enumerate(Entities)
    )
    LengthRefs = (ConstraintRef(Entities[0].id, "start"), ConstraintRef(Entities[0].id, "end"))
    WidthRefs = (
        (ConstraintRef(Entities[3].id, "end"), ConstraintRef(Entities[3].id, "start"))
        if NegativeV
        else (ConstraintRef(Entities[1].id, "start"), ConstraintRef(Entities[1].id, "end"))
    )
    LengthRelations = tuple(
        SketchRelation(
            f"relation/length/{Index}",
            "distance",
            References,
            ParameterId,
        )
        for Index, (References, ParameterId) in enumerate(
            zip((LengthRefs, WidthRefs), ParameterIds, strict=True)
        )
    )
    return Sketch(
        SketchId,
        SketchName,
        PlaneId,
        Entities,
        constraints=(*AxisRelations, *LengthRelations),
        parameter_ids=ParameterIds,
        closed_profile_entity_ids=(tuple(Entity.id for Entity in Entities),),
    )
