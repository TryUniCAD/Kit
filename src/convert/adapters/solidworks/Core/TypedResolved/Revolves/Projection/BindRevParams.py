from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue


# the feature must expose its actual positive radian driver without trusting keyword units or stale scalar matches
def BindRevParams(
    Values: tuple[Parameter, ...], OwnerValue: RevolveOwner
) -> tuple[Parameter, ...]:
    NativeId = NativeNodeId(OwnerValue.NodeValue)
    AngleValue = OwnerValue.AngleValue
    FeatureId = f"sldprt:feature:{NativeId}"
    ParameterId = f"sldprt:parameter:{NativeId}:{AngleValue.NameValue}"
    Existing = tuple(Value for Value in Values if Value.owner_id == FeatureId)
    if len(Existing) > 1 or any(Value.id != ParameterId for Value in Existing):
        raise ValueError(
            "ordinary revolve has another unresolved neutral parameter owner"
        )
    Attributes = dict(Existing[0].attributes) if Existing else {}
    ParameterData = Parameter(
        id=ParameterId,
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
                    "slot": "f8d8.f18",
                },
            }
        ),
    )
    return tuple(
        ParameterData if Value.id == ParameterId else Value for Value in Values
    ) + (() if Existing else (ParameterData,))
