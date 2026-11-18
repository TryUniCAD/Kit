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
) -> Sketch:
    Corners = (
        PlaneVector(0.0, 0.0),
        PlaneVector(LengthValue, 0.0),
        PlaneVector(LengthValue, WidthValue),
        PlaneVector(0.0, WidthValue),
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
    LengthRelations = tuple(
        SketchRelation(
            f"relation/length/{Index}",
            "distance",
            (ConstraintRef(Edge.id, "start"), ConstraintRef(Edge.id, "end")),
            ParameterId,
        )
        for Index, (Edge, ParameterId) in enumerate(
            zip(Entities[:2], ParameterIds, strict=True)
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
