from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import SketchEntity


# contour mapping must preserve actual endpoint incidence while excluding unrepresented construction or fixed geometry
def ReadSourceLine(
    EntityValue: SketchEntity, UnitScale: float
) -> tuple[tuple[float, float], tuple[float, float]]:
    Geometry = EntityValue.geometry
    if (
        type(Geometry) is not LineGeometry
        or EntityValue.kind != "line"
        or EntityValue.fixed
        or EntityValue.construction
    ):
        raise ValueError("source stock requires ordinary unfixed nonconstruction lines")
    StartValue = (
        RequireScalar(Geometry.start.x) * UnitScale,
        RequireScalar(Geometry.start.y) * UnitScale,
    )
    EndValue = (
        RequireScalar(Geometry.end.x) * UnitScale,
        RequireScalar(Geometry.end.y) * UnitScale,
    )
    if StartValue == EndValue or (
        StartValue[0] != EndValue[0] and StartValue[1] != EndValue[1]
    ):
        raise ValueError("source stock line is degenerate or not axis aligned")
    return StartValue, EndValue
