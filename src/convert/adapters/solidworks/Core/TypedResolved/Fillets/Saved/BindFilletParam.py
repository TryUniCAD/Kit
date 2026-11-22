from dataclasses import replace as ReplaceValue
from math import isclose as IsClose

from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue


# the public editable dimension must retain its live parameter rather than the keyword radius approximation
def BindFilletParam(ParamValue: Parameter, History: FilletHistory) -> Parameter:
    DriveValue = History.DriveValue
    Radius = DriveValue.RadiusValue * 1000.0
    if (
        ParamValue.name != "D1"
        or ParamValue.role != ParameterRole.KDriving
        or ParamValue.expression is not None
        or ParamValue.value.unit != "mm"
        or not isinstance(ParamValue.value.value, (int, float))
        or not IsClose(ParamValue.value.value, Radius, rel_tol=1e-13)
    ):
        raise ValueError("saved fillet public D1 differs from its actual live driver")
    LinkValue = History.LinkValue
    OwnerValue = NativeNodeSpan(LinkValue, DriveValue.ParamValue)
    return ReplaceValue(
        ParamValue,
        value=ParameterValue(Radius, ValueKind.KLength, "mm"),
        provenance=TypedProvenance(OwnerValue, ParamValue.id),
        attributes=FreezeMapping(
            {
                **ParamValue.attributes,
                "typed_parameter_owner": OwnerValue,
                "typed_dimension_owner": NativeNodeSpan(
                    LinkValue, DriveValue.DimensionValue
                ),
                "typed_display_owner": NativeNodeSpan(
                    LinkValue, DriveValue.DisplayValue
                ),
            }
        ),
    )
