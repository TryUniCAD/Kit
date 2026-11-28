from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ExactMm import ExactMm
from interchange.Core.Common import FreezeMapping
from interchange.Records.RecordParameter import Parameter
from interchange.geometry.Models.Sketch import Sketch


# the owned sketch dimensions retain their source identities and exact wire lengths in the neutral construction copy
def ReadEqDrivers(
    SketchValue: Sketch, Parameters: tuple[Parameter, ...]
) -> tuple[Parameter, tuple[Parameter, ...]]:
    Dependent = tuple(Value for Value in Parameters if Value.expression is not None)
    Drivers = {Value.id: Value for Value in Parameters if Value.expression is None}
    if (
        len(Dependent) != 1
        or len(SketchValue.parameter_ids) != 2
        or set(SketchValue.parameter_ids) != Drivers.keys()
    ):
        raise ValueError(
            "SOLIDWORKS cold equation lacks its two typed sketch dimensions"
        )
    WidthId, HeightId = SketchValue.parameter_ids
    return Dependent[0], (
        ReadEqDriver(Drivers[WidthId], SketchValue.id),
        ReadEqDriver(Drivers[HeightId], SketchValue.id),
    )


# normalize the exact metre wire representation without substituting a cached equality
def ReadEqDriver(Driver: Parameter, SketchId: str) -> Parameter:
    DisplayValue = Driver.value.value
    if (
        Driver.attributes.get("native_unit") != "m"
        or Driver.value.unit != "mm"
        or type(DisplayValue) is not float
    ):
        raise ValueError("SOLIDWORKS cold equation requires exact typed sketch lengths")
    return ReplaceValue(
        Driver,
        owner_id=SketchId,
        value=ReplaceValue(
            Driver.value,
            value=ExactMm(Driver.attributes.get("native_value"), DisplayValue),
        ),
        attributes=FreezeMapping(),
        provenance=None,
    )
