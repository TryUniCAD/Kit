from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternDim import (
    PatternDim,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue


# the parameter keeps its neutral identity and actual live archive ownership
def MakePatParam(
    Existing: Parameter, Driver: PatternDim, LinkValue: NativeLink
) -> Parameter:
    if (
        Existing.name != Driver.NativeName
        or Existing.expression is not None
        or Existing.role != ParameterRole.KDriving
    ):
        raise ValueError(
            "pattern has another active neutral parameter owner or relation"
        )
    IsCount = Driver.NativeName == "D1"
    if IsCount and type(Driver.LiveValue) is not int:
        raise ValueError("pattern count has no integral live parameter")
    Quantity = (
        ParameterValue(Driver.LiveValue, ValueKind.KInteger)
        if IsCount
        else ParameterValue(Driver.LiveValue * 1000.0, ValueKind.KLength, "mm")
    )
    ProofValue = {
        **NativeNodeSpan(LinkValue, Driver.ParameterValue),
        "slot": Driver.SlotName,
        "value_field": "f58",
        "dimension_id": Driver.DimensionValue.FieldsValue["f50"],
        "dimension_index": Driver.DimensionValue.IndexValue,
        "handle_index": Driver.HandleValue.IndexValue,
        "display_index": Driver.DisplayValue.IndexValue,
    }
    return ReplaceValue(
        Existing,
        value=Quantity,
        provenance=TypedProvenance(ProofValue, Existing.id),
        attributes=FreezeMapping(
            {
                **Existing.attributes,
                "native_value": Driver.LiveValue,
                "native_unit": "" if IsCount else "m",
                "typed_archive_owner": ProofValue,
                "native_display_cache": Driver.CacheValue,
            }
        ),
    )
