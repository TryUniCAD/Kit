from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolveShape import (
    RevolveShape,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch


# the qualified revolve must preserve one real rectangle and its separate unfixed construction line without inferring a contour
def ReadRevShape(SketchValue: Sketch, AxisEntityId: str) -> RevolveShape:
    if (
        SketchValue.suppressed
        or SketchValue.attributes
        or SketchValue.parameter_ids
        or len(SketchValue.entities) != 5
        or len(SketchValue.constraints) not in (4, 5)
        or len(SketchValue.closed_profile_entity_ids) != 1
    ):
        raise ValueError(
            "revolve requires five lines and supported actual contour relations"
        )
    EntityValues = {Entity.id: Entity for Entity in SketchValue.entities}
    OrderValue = SketchValue.closed_profile_entity_ids[0]
    if (
        len(OrderValue) != 4
        or len(set(OrderValue)) != 4
        or not set(OrderValue).issubset(EntityValues)
        or set(EntityValues) - set(OrderValue) != {AxisEntityId}
    ):
        raise ValueError(
            "revolve requires one explicit four edge contour outside its axis"
        )
    VerticesValue: list[tuple[float, float]] = []
    EndValues: list[tuple[float, float]] = []
    for EntityId in (*OrderValue, AxisEntityId):
        EntityValue = EntityValues[EntityId]
        Geometry = EntityValue.geometry
        if (
            EntityValue.kind != GeometryKind.KLine
            or type(Geometry) is not LineGeometry
            or EntityValue.fixed
            or EntityValue.attributes
            or EntityValue.construction != (EntityId == AxisEntityId)
        ):
            raise ValueError(
                "revolve requires ordinary lines and one real construction axis"
            )
        VerticesValue.append(
            (
                RequireScalar(Geometry.start.x) * 0.001,
                RequireScalar(Geometry.start.y) * 0.001,
            )
        )
        EndValues.append(
            (
                RequireScalar(Geometry.end.x) * 0.001,
                RequireScalar(Geometry.end.y) * 0.001,
            )
        )
    AxisStart, AxisEnd = VerticesValue.pop(), EndValues.pop()
    if any(
        EndValue != VerticesValue[(IndexValue + 1) % 4]
        for IndexValue, EndValue in enumerate(EndValues)
    ):
        raise ValueError("revolve contour must retain exact joined endpoint identity")
    Vertices = PolygonInput(tuple(VerticesValue), 19000).VerticesValue
    FirstValues = {PointValue[0] for PointValue in Vertices}
    SecondValues = {PointValue[1] for PointValue in Vertices}
    if (
        len(FirstValues) != 2
        or len(SecondValues) != 2
        or set(Vertices)
        != {
            (FirstValue, SecondValue)
            for FirstValue in FirstValues
            for SecondValue in SecondValues
        }
        or AxisStart[0] != AxisEnd[0]
        or AxisStart[0] >= min(FirstValues)
        or AxisEnd[1] - AxisStart[1] < 1e-8
    ):
        raise ValueError(
            "revolve requires a rectangle right of an upward construction axis"
        )
    return RevolveShape(Vertices, AxisStart, AxisEnd, AxisEntityId)
