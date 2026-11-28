from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryConics import EllipseGeometry
from interchange.geometry.Models.Sketch import Sketch


# the cold profile must preserve its only authored entity and have a genuinely full closed ellipse
def ReadEllipGeom(SketchValue: Sketch) -> EllipseGeometry:
    if (
        len(SketchValue.entities) != 1
        or SketchValue.constraints
        or SketchValue.parameter_ids
        or SketchValue.suppressed
        or SketchValue.attributes
        or SketchValue.provenance
    ):
        raise ValueError("cold ellipse requires one free ordinary Front sketch")
    (EntityValue,) = SketchValue.entities
    GeometryValue = EntityValue.geometry
    if (
        type(GeometryValue) is not EllipseGeometry
        or EntityValue.kind != GeometryKind.KEllipse
        or SketchValue.closed_profile_entity_ids != ((EntityValue.id,),)
        or EntityValue.construction
        or EntityValue.fixed
        or EntityValue.attributes
        or EntityValue.provenance
    ):
        raise ValueError("cold ellipse requires its actual free full closed entity")
    return GeometryValue
