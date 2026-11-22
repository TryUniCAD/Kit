from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch


# a neutral line loop must give the native profile the actual ordered segments and their shared endpoints
def ReadLineLoop(
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
    CountValue = len(SketchValue.entities)
    if not 3 <= CountValue <= 64 or len(SketchValue.closed_profile_entity_ids) != 1:
        raise ValueError(
            "plain boss requires one closed loop of three to sixty four lines"
        )
    OrderValue = SketchValue.closed_profile_entity_ids[0]
    EntitiesValue = {
        EntityValue.id: EntityValue for EntityValue in SketchValue.entities
    }
    if (
        len(OrderValue) != CountValue
        or len(set(OrderValue)) != CountValue
        or set(OrderValue) != set(EntitiesValue)
    ):
        raise ValueError("the loop must own every actual line entity exactly once")
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
                "plain boss requires ordinary nonconstruction nonfixed lines"
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
        EndValues[IndexValue] != VerticesValue[(IndexValue + 1) % CountValue]
        for IndexValue in range(CountValue)
    ):
        raise ValueError("the lines must retain exact modeled closed endpoint identity")
    return tuple(VerticesValue)
