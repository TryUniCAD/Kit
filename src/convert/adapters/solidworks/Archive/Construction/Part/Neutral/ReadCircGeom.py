from convert.adapters.solidworks.Archive.Construction.Circles.CircleInput import (
    CircleInput,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import Sketch


# the admitted profile must retain the sole actual closed analytic circle and its positive sketch radius
def ReadCircGeom(SketchValue: Sketch, UnitScale: float) -> CircleInput:
    if (
        SketchValue.suppressed
        or SketchValue.attributes
        or len(SketchValue.entities) != 1
    ):
        raise ValueError("circle boss requires one active unextended circle sketch")
    EntityValue = SketchValue.entities[0]
    Geometry = EntityValue.geometry
    if (
        EntityValue.kind != GeometryKind.KCircle
        or type(Geometry) is not CircleGeometry
        or EntityValue.construction
        or EntityValue.fixed
        or EntityValue.attributes
        or SketchValue.closed_profile_entity_ids != ((EntityValue.id,),)
    ):
        raise ValueError(
            "circle boss requires its actual ordinary closed circle entity"
        )
    CenterValue = (
        RequireScalar(Geometry.center.x) * UnitScale,
        RequireScalar(Geometry.center.y) * UnitScale,
    )
    return CircleInput(CenterValue, RequireScalar(Geometry.radius) * UnitScale, 19000)
