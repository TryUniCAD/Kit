from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite

from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter


# the displayed millimetres must agree with the exact owner metre value that generates the archive
def ReadPatLength(DriverValue: Parameter, OwnerId: str, NameValue: str) -> Parameter:
    NativeValue = DriverValue.attributes.get("native_value")
    if (
        DriverValue.owner_id != OwnerId
        or DriverValue.name != NameValue
        or DriverValue.role is not ParameterRole.KDriving
        or DriverValue.value.kind is not ValueKind.KLength
        or DriverValue.value.unit != "mm"
        or DriverValue.attributes.get("native_unit") != "m"
        or type(NativeValue) is not float
        or not IsFinite(NativeValue)
        or NativeValue <= 0.0
        or DriverValue.value.value not in (NativeValue * 1000.0, NativeValue / 0.001)
    ):
        raise ValueError("SOLIDWORKS cold pattern lacks its exact length driver")
    return ReplaceValue(
        DriverValue,
        value=ReplaceValue(DriverValue.value, value=NativeValue, unit="m"),
        provenance=None,
        attributes=FreezeMapping(),
    )
