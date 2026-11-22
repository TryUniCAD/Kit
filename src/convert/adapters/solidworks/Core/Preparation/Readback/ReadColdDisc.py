from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.IsCircDiameter import (
    IsCircDiameter,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ExactMm import ExactMm
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import Parameter


# the original circle comes from its typed centre and its separately owned driving radial dimension
def ReadColdDisc(
    SketchValue: Sketch, Driver: Parameter, SketchOwner: str
) -> tuple[Sketch, Parameter]:
    if (
        len(SketchValue.entities) != 1
        or SketchValue.parameter_ids != (Driver.id,)
        or Driver.owner_id != SketchOwner
        or Driver.attributes.get("native_unit") != "m"
        or Driver.value.unit != "mm"
        or type(Driver.value.value) is not float
    ):
        raise ValueError("SOLIDWORKS cold circle requires its exact radial driver")
    (Entity,) = SketchValue.entities
    IsDiameter = IsCircDiameter(SketchValue, Entity.id, Driver.id)
    Radial = ExactMm(
        Driver.attributes.get("native_value"), Driver.value.value, Multiplied=True
    )
    return ReplaceValue(
        SketchValue,
        entities=(ReadDiscEntity(Entity, Radial / (2 if IsDiameter else 1)),),
        constraints=tuple(
            ReplaceValue(Relation, provenance=None)
            for Relation in SketchValue.constraints
        ),
        attributes=FreezeMapping(),
        provenance=None,
    ), ReplaceValue(
        Driver,
        value=ReplaceValue(Driver.value, value=Radial),
        owner_id=SketchValue.id,
        attributes=FreezeMapping(),
        provenance=None,
    )


# measured centre displays can differ from the exact millimetre input by one binary64 step
def ReadDiscEntity(Entity: SketchEntity, Radius: float) -> SketchEntity:
    Geometry = Entity.geometry
    Center = Entity.attributes.get("native_center_m")
    if type(Geometry) is not CircleGeometry or type(Center) is not tuple:
        raise ValueError("SOLIDWORKS cold circle lacks its typed centre")
    CenterValues = CastValue(tuple[object, ...], Center)
    if len(CenterValues) != 2:
        raise ValueError("SOLIDWORKS cold circle lacks its typed centre")
    return ReplaceValue(
        Entity,
        geometry=CircleGeometry(
            PlaneVector(
                ExactMm(CenterValues[0], Geometry.center.x, Multiplied=True),
                ExactMm(CenterValues[1], Geometry.center.y, Multiplied=True),
            ),
            Radius,
        ),
        attributes=FreezeMapping(),
        provenance=None,
    )
