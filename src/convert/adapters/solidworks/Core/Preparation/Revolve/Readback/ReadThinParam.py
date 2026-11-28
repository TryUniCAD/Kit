from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.Readback.ExactMm import ExactMm
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter


# the wall driver keeps its exact physical metres when the displayed millimetres are rounded
def ReadThinParam(DriverValue: Parameter) -> Parameter:
    ValueData = DriverValue.value
    if ValueData.kind == ValueKind.KLength:
        Native = RequireScalar(DriverValue.attributes.get("native_value"))
        if DriverValue.attributes.get("native_unit") != "m":
            raise ValueError("thin revolve public wall differs from its typed length")
        ValueData = ReplaceValue(
            ValueData,
            value=ExactMm(Native, RequireScalar(ValueData.value), IsScaled=True),
        )
    return ReplaceValue(
        DriverValue, value=ValueData, attributes=FreezeMapping(), provenance=None
    )
