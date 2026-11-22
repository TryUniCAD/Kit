from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite

from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter


# the three typed drivers retain metres while their reader layouts display millimetres differently
def ReadOffDrive(
    Driver: Parameter, OwnerId: str, KindValue: str, *, IsRadial: bool = False
) -> Parameter:
    NativeValue = Driver.attributes.get("native_value")
    OwnerValue = NativeRecord(Driver.attributes.get("typed_archive_owner"))
    if (
        Driver.name != "D1"
        or Driver.owner_id != OwnerId
        or Driver.role != ParameterRole.KDriving
        or Driver.expression is not None
        or Driver.value.unit != "mm"
        or Driver.value.kind != ValueKind.KLength
        or Driver.attributes.get("native_unit") != "m"
        or Driver.attributes.get("dimension_kind") != KindValue
        or OwnerValue.get("class") != "moLengthParameter_c"
        or OwnerValue.get("value_field") != "f58"
        or type(NativeValue) is not float
        or not IsFinite(NativeValue)
        or NativeValue <= 0
        or Driver.value.value
        != (NativeValue * 1000.0 if IsRadial else NativeValue / 0.001)
    ):
        raise ValueError("SOLIDWORKS offset readback lacks its exact typed D1")
    return ReplaceValue(
        Driver,
        value=ReplaceValue(Driver.value, unit="m", value=NativeValue),
        attributes=FreezeMapping(),
        provenance=None,
    )
