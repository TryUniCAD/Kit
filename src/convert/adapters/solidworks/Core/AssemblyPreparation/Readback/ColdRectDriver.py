from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Readback.ExactMm import ExactMm
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole
from interchange.Records.RecordParameter import Parameter


# exact sketch lengths follow their owned typed metre value and actual public sketch parameter
def ColdRectDriver(Driver: Parameter, OwnerId: str, SketchId: str) -> Parameter:
    Display = Driver.value.value
    Native = Driver.attributes.get("native_value")
    if (
        Driver.owner_id != OwnerId
        or Driver.role != ParameterRole.KDriving
        or Driver.expression is not None
        or Driver.value.unit != "mm"
        or type(Display) is not float
        or Driver.attributes.get("native_unit") != "m"
        or type(Native) is not float
        or Display.hex() not in ((Native * 1000.0).hex(), (Native / 0.001).hex())
    ):
        raise ValueError("reopened rectangle lacks its exact sketch distance driver")
    Value = ReplaceValue(Driver.value, value=ExactMm(Native, Native / 0.001))
    return ReplaceValue(
        Driver,
        owner_id=SketchId,
        value=Value,
        provenance=None,
        attributes=FreezeMapping(),
    )
