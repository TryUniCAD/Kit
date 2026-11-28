from dataclasses import replace as ReplaceValue
from math import isclose as IsClose
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.Readback.ExactMm import ExactMm
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.Models.Sketch import ConstraintRef, Sketch
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter


# metre words must agree with the actual displayed point before restoring the original constructor units
def ExactCircCoord(Metres: object, Millimetres: float) -> float:
    if type(Metres) is not float or (Metres * 1000.0).hex() != Millimetres.hex():
        raise ValueError(
            "SOLIDWORKS circle readback centre disagrees with its typed point"
        )
    return ExactMm(Metres, Metres / 0.001)


# the ordinary constructor uses a centre subelement while the source retains its distinct linked point
def ReadCircSketch(SketchValue: Sketch, Driver: Parameter) -> Sketch:
    ArcValue, PointValue = SketchValue.entities
    Radial, Fixed = SketchValue.constraints
    if (
        type(ArcValue.geometry) is not CircleGeometry
        or type(PointValue.geometry) is not PointGeometry
        or ArcValue.geometry.center != PointValue.geometry.point
        or PointValue.construction
        or PointValue.fixed
        or Radial.kind not in ("radius", "diameter")
        or Radial.references != (ConstraintRef(ArcValue.id),)
        or Radial.parameter_id != Driver.id
        or Fixed.kind != "fixed"
        or Fixed.references != (ConstraintRef(PointValue.id),)
    ):
        raise ValueError("SOLIDWORKS circle readback lacks its actual fixed centre")
    Metres = ArcValue.attributes.get("native_center_m")
    if type(Metres) is not tuple:
        raise ValueError("SOLIDWORKS circle readback requires its exact centre")
    Coordinates = CastValue(tuple[object, ...], Metres)
    if len(Coordinates) != 2:
        raise ValueError("SOLIDWORKS circle readback requires two exact coordinates")
    CenterValue = ArcValue.geometry.center
    Position = PlaneVector(
        ExactCircCoord(Coordinates[0], CenterValue.x),
        ExactCircCoord(Coordinates[1], CenterValue.y),
    )
    Radius = RequireScalar(Driver.value.value) / (2 if Radial.kind == "diameter" else 1)
    if not IsClose(
        ArcValue.geometry.radius, Radius * 1000.0, rel_tol=1e-12, abs_tol=1e-10
    ):
        raise ValueError("SOLIDWORKS circle readback radius differs from its driver")
    Geometry = CircleGeometry(Position, ExactMm(Radius, Radius / 0.001))
    return ReplaceValue(
        SketchValue,
        entities=(
            ReplaceValue(
                ArcValue, geometry=Geometry, attributes=FreezeMapping(), provenance=None
            ),
        ),
        constraints=(
            Radial,
            ReplaceValue(Fixed, references=(ConstraintRef(ArcValue.id, "center"),)),
        ),
        attributes=FreezeMapping(),
        provenance=None,
    )
