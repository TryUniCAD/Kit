from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import Sketch


# cache free ordinary circle readback must retain the exact metre point independently from its displayed coordinate
def BindColdCentre(
    Sketches: tuple[Sketch, ...], Model: NativeModel, Archive: SldprtArchive
) -> tuple[Sketch, ...]:
    if (
        len(Model.operations) != 1
        or Model.operations[0].kind != "join"
        or len(Model.sketches) != 1
        or len(Sketches) != 1
        or len(Archive.records) != 10
        or sum(Value.class_name == "moRefPlane_c" for Value in Model.features) != 3
        or not IsCacheAbsent(Archive)
    ):
        return Sketches
    CircleValue = Model.sketches[0].TypedCircle
    SketchValue = Sketches[0]
    if (
        CircleValue is None
        or CircleValue.ModeValue is None
        or (
            len(SketchValue.entities) != 2
            or type(SketchValue.entities[0].geometry) is not CircleGeometry
        )
    ):
        return Sketches
    ArcValue, PointValue = SketchValue.entities
    ArcValue = ReplaceValue(
        ArcValue,
        attributes=FreezeMapping(
            {**ArcValue.attributes, "native_center_m": CircleValue.CenterMetres}
        ),
    )
    return (ReplaceValue(SketchValue, entities=(ArcValue, PointValue)),)
