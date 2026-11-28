from dataclasses import replace as ReplaceValue

from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch


# the fixed standalone native point must actually be the centre of the radial circle
def ProjectOffSk(SketchValue: Sketch, DriverId: str, Radius: float) -> Sketch:
    Circle, Center = SketchValue.entities
    Radial, Fixed = SketchValue.constraints
    if (
        type(Circle.geometry) is not CircleGeometry
        or type(Center.geometry) is not PointGeometry
        or Center.kind != GeometryKind.KPoint
        or Center.geometry.point != Circle.geometry.center
        or Center.construction
        or Center.fixed
        or Circle.geometry.radius != Radius * 1000.0
        or Radial.kind != "radius"
        or Radial.parameter_id != DriverId
        or Fixed.kind != "fixed"
        or Fixed.references != (ConstraintRef(Center.id),)
    ):
        raise ValueError(
            "SOLIDWORKS offset readback lacks its actual fixed circle centre"
        )
    return ReplaceValue(
        SketchValue,
        entities=(ReplaceValue(Circle, attributes=FreezeMapping(), provenance=None),),
        constraints=(
            Radial,
            ReplaceValue(Fixed, references=(ConstraintRef(Circle.id, "center"),)),
        ),
        attributes=FreezeMapping(),
        provenance=None,
    )
