from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite

from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter


# the linked metre value preserves the real radius or independent extrusion depth owner
def ReadCircDrive(
    Driver: Parameter, OwnerId: str, NameValue: str, *, Radial: bool = False
) -> Parameter:
    NativeValue = Driver.attributes.get("native_value")
    OwnerValue = NativeRecord(Driver.attributes.get("typed_archive_owner"))
    if (
        Driver.name != NameValue
        or Driver.owner_id != OwnerId
        or Driver.role != ParameterRole.KDriving
        or Driver.expression is not None
        or Driver.value.kind != ValueKind.KLength
        or Driver.value.unit != "mm"
        or Driver.attributes.get("native_unit") != "m"
        or Driver.attributes.get("dimension_kind") != "length"
        or OwnerValue.get("class") != "moLengthParameter_c"
        or OwnerValue.get("value_field") != "f58"
        or type(NativeValue) is not float
        or not IsFinite(NativeValue)
        or NativeValue <= 0.0
        or Driver.value.value
        != (NativeValue * 1000.0 if Radial else NativeValue / 0.001)
    ):
        raise ValueError("SOLIDWORKS circle readback lacks its exact typed length")
    return ReplaceValue(
        Driver,
        value=ReplaceValue(Driver.value, unit="m", value=NativeValue),
        attributes=FreezeMapping(),
        provenance=None,
    )
