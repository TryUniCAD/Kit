from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import PointGeometry
from interchange.geometry.Models.Sketch import SketchEntity


# the intrinsic fixed origin is independent of any movable sketch point at identical coordinates
def IsFixedOrigin(Entity: SketchEntity) -> bool:
    Origin = Entity.provenance
    return (
        Entity.fixed
        and Entity.kind == GeometryKind.KPoint
        and isinstance(Entity.geometry, PointGeometry)
        and Entity.geometry.point.x == Entity.geometry.point.y == 0.0
        and Entity.attributes.get("fusion.point_is_origin") is True
        and Origin is not None
        and Origin.adapter == "fusion.f3d"
        and Entity.id == f"fusion-sketch-entity-{Origin.native_id}"
    )
