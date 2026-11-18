from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch


# rectangle topology must follow explicit neutral entity references rather than a heuristic native stream scan or endpoint fitting
def ReadRectSketch(
    SketchValue: Sketch, UnitScale: float
) -> tuple[tuple[float, float], ...]:
    if (
        SketchValue.suppressed
        or SketchValue.constraints
        or SketchValue.parameter_ids
        or SketchValue.attributes
    ):
        raise ValueError(
            "plain boss requires an unconstrained unextended active sketch"
        )
    if (
        len(SketchValue.entities) != 4
        or len(SketchValue.closed_profile_entity_ids) != 1
    ):
        raise ValueError("plain boss requires one explicit four segment closed profile")
    OrderValue = SketchValue.closed_profile_entity_ids[0]
    EntitiesValue = {
        EntityValue.id: EntityValue for EntityValue in SketchValue.entities
    }
    if (
        len(OrderValue) != 4
        or len(set(OrderValue)) != 4
        or set(OrderValue) != set(EntitiesValue)
    ):
        raise ValueError(
            "rectangle loop must own every actual line entity exactly once"
        )
    VerticesValue: list[tuple[float, float]] = []
    EndValues: list[tuple[float, float]] = []
    for EntityId in OrderValue:
        EntityValue = EntitiesValue[EntityId]
        GeometryValue = EntityValue.geometry
        if (
            EntityValue.kind != GeometryKind.KLine
            or type(GeometryValue) is not LineGeometry
            or EntityValue.construction
            or EntityValue.fixed
            or EntityValue.attributes
        ):
            raise ValueError(
                "plain boss requires four ordinary nonconstruction nonfixed line segments"
            )
        VerticesValue.append(
            (
                RequireScalar(GeometryValue.start.x) * UnitScale,
                RequireScalar(GeometryValue.start.y) * UnitScale,
            )
        )
        EndValues.append(
            (
                RequireScalar(GeometryValue.end.x) * UnitScale,
                RequireScalar(GeometryValue.end.y) * UnitScale,
            )
        )
    if any(
        EndValues[IndexValue] != VerticesValue[(IndexValue + 1) % 4]
        for IndexValue in range(4)
    ):
        raise ValueError(
            "rectangle lines must retain exact modeled closed endpoint identity"
        )
    InputValue = PolygonInput(tuple(VerticesValue), 19000)
    if (
        len({PointValue[0] for PointValue in VerticesValue}) != 2
        or len({PointValue[1] for PointValue in VerticesValue}) != 2
    ):
        raise ValueError(
            "first plain boss profile requires a local axis aligned rectangle"
        )
    return InputValue.VerticesValue
