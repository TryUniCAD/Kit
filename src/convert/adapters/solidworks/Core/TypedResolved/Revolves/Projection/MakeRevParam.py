from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAngle import (
    RevolveAngle,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue


# actual angular owners must replace heuristic keyword values without losing their metadata
def MakeRevParam(
    ParamId: str,
    FeatureId: str,
    NativeId: int,
    AngleValue: RevolveAngle,
    SlotName: str,
    Existing: Parameter | None,
) -> Parameter:
    Attributes = {} if Existing is None else dict(Existing.attributes)
    return Parameter(
        id=ParamId,
        name=AngleValue.NameValue,
        value=ParameterValue(AngleValue.RadiansValue, ValueKind.KAngle, "rad"),
        role=ParameterRole.KDriving,
        owner_id=FeatureId,
        provenance=TypedProvenance(
            AngleValue.OwnerValue, f"{NativeId}:{AngleValue.NameValue}"
        ),
        attributes=FreezeMapping(
            {
                **Attributes,
                "native_value": AngleValue.RadiansValue,
                "native_unit": "rad",
                "native_role": "driving",
                "dimension_kind": "angle",
                "native_dimension_id": AngleValue.DimensionValue.FieldsValue["f50"],
                "native_display_index": AngleValue.DisplayValue.IndexValue,
                "native_handle_index": AngleValue.HandleValue.IndexValue,
                "native_parameter_class": AngleValue.ParameterValue.ClassValue.NameValue,
                "native_parameter_flags": AngleValue.ParameterValue.FieldsValue.get(
                    "f28"
                ),
                "typed_archive_owner": {
                    **AngleValue.OwnerValue,
                    "value_field": "f58",
                    "slot": SlotName,
                },
            }
        ),
    )
