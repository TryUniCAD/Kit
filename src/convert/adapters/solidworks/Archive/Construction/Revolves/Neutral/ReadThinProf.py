from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolveShape import (
    RevolveShape,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity


# independent sketch lines must retain their point order and construction distinction
def ReadLinePoints(
    EntityValue: SketchEntity, IsAxis: bool
) -> tuple[tuple[float, float], tuple[float, float]]:
    Geometry = EntityValue.geometry
    if (
        EntityValue.kind != GeometryKind.KLine
        or type(Geometry) is not LineGeometry
        or EntityValue.construction is not IsAxis
        or EntityValue.fixed
        or EntityValue.attributes
    ):
        raise ValueError("thin profile requires its plain line and construction axis")
    StartPoint, EndPoint = Geometry.start, Geometry.end
    return (
        (RequireScalar(StartPoint.x) * 0.001, RequireScalar(StartPoint.y) * 0.001),
        (RequireScalar(EndPoint.x) * 0.001, RequireScalar(EndPoint.y) * 0.001),
    )


# only the measured vertically ordered open line and distinct longer centreline are admissible
def ReadThinProf(SketchValue: Sketch, AxisId: str) -> RevolveShape:
    if (
        len(SketchValue.entities) != 2
        or SketchValue.constraints
        or SketchValue.closed_profile_entity_ids
        or SketchValue.attributes
        or SketchValue.suppressed
        or SketchValue.parameter_ids
    ):
        raise ValueError("thin profile must contain two actual independent open lines")
    WallValue, AxisValue = SketchValue.entities
    if AxisValue.id != AxisId:
        raise ValueError("thin sketch axis must follow its open body line")
    StartValue, EndValue = ReadLinePoints(AxisValue, True)
    EdgeValue = ReadLinePoints(WallValue, False)
    (StartX, StartY), (EndXValue, EndYValue) = EdgeValue
    if not (
        StartValue[0] == EndValue[0] < StartX == EndXValue
        and StartValue[1] < StartY < EndYValue < EndValue[1]
    ):
        raise ValueError("thin profile and axis must be separate ordered axial lines")
    return RevolveShape(EdgeValue, StartValue, EndValue, AxisId)
