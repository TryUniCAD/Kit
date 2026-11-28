from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.MakeRevParam import (
    MakeRevParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinRevOwner import (
    ThinRevOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.ThinWallOwner import (
    ThinWallOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue


# an active wall is an editable model parameter with the precise native chain provenance
def MakeWallParam(
    LinkValue: NativeLink,
    OwnerValue: ThinWallOwner,
    FeatureId: str,
    NativeId: int,
    Existing: Mapping[str, Parameter],
) -> Parameter:
    NameValue = OwnerValue.NameValue
    ParamId = f"sldprt:parameter:{NativeId}:{NameValue}"
    PriorValue = Existing.get(ParamId)
    Attributes = {} if PriorValue is None else dict(PriorValue.attributes)
    SpanValue = NativeNodeSpan(LinkValue, OwnerValue.ParameterValue)
    return Parameter(
        id=ParamId,
        name=NameValue,
        value=ParameterValue(1000.0 * OwnerValue.MetresValue, ValueKind.KLength, "mm"),
        role=ParameterRole.KDriving,
        owner_id=FeatureId,
        provenance=TypedProvenance(SpanValue, f"{NativeId}:{NameValue}"),
        attributes=FreezeMapping(
            {
                **Attributes,
                "native_value": OwnerValue.MetresValue,
                "native_unit": "m",
                "native_role": "driving",
                "dimension_kind": "length",
                "native_dimension_id": OwnerValue.DimensionValue.FieldsValue["f50"],
                "native_display_index": OwnerValue.DisplayValue.IndexValue,
                "native_handle_index": OwnerValue.HandleValue.IndexValue,
                "typed_archive_owner": {
                    **SpanValue,
                    "value_field": "f58",
                    "slot": "f8f0.f08" if NameValue == "D3" else "f8f0.f10",
                },
            }
        ),
    )


# the actual angular and wall role order must replace only matching heuristic rows
def BindThinParams(
    Values: tuple[Parameter, ...], LinkValue: NativeLink, OwnerValue: ThinRevOwner
) -> tuple[tuple[Parameter, ...], tuple[str, ...]]:
    SweepValue = OwnerValue.SweepValue
    NativeId = NativeNodeId(SweepValue.NodeValue)
    FeatureId = f"sldprt:feature:{NativeId}"
    AngleId = f"sldprt:parameter:{NativeId}:D1"
    Existing = {Value.id: Value for Value in Values}
    Parameters = (
        MakeRevParam(
            AngleId,
            FeatureId,
            NativeId,
            SweepValue.EndValue.AlongValue,
            "f8d8.f18",
            Existing.get(AngleId),
        ),
        *(
            MakeWallParam(LinkValue, WallValue, FeatureId, NativeId, Existing)
            for WallValue in OwnerValue.WallValues
        ),
    )
    Replacements = {ParamValue.id: ParamValue for ParamValue in Parameters}
    if any(
        (Value.owner_id == FeatureId) != (Value.id in Replacements) for Value in Values
    ):
        raise ValueError(
            "SOLIDWORKS thin revolve has an additional unresolved parameter owner"
        )
    return (
        tuple(Replacements.get(Value.id, Value) for Value in Values)
        + tuple(Value for Value in Parameters if Value.id not in Existing),
        tuple(Replacements),
    )
