from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Projection.MakeRevParam import (
    MakeRevParam,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAngle import (
    RevolveAngle,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)
from interchange.Records.RecordParameter import Parameter


# driver references follow actual end slot order while existing document parameter order stays stable
def BindRevParams(
    Values: tuple[Parameter, ...], OwnerValue: RevolveOwner
) -> tuple[tuple[Parameter, ...], tuple[str, ...]]:
    NativeId = NativeNodeId(OwnerValue.NodeValue)
    EndValue = OwnerValue.EndValue
    FeatureId = f"sldprt:feature:{NativeId}"
    AngularValues: tuple[tuple[str, RevolveAngle], ...] = (
        ("f8d8.f18", EndValue.AlongValue),
    )
    if EndValue.AgainstValue is not None:
        AngularValues += (("f8d8.f20", EndValue.AgainstValue),)
    Existing = {Value.id: Value for Value in Values}
    BoundParams: dict[str, Parameter] = {}
    for SlotName, AngleValue in AngularValues:
        ParamId = f"sldprt:parameter:{NativeId}:{AngleValue.NameValue}"
        BoundParams[ParamId] = MakeRevParam(
            ParamId, FeatureId, NativeId, AngleValue, SlotName, Existing.get(ParamId)
        )
    if any(
        (Value.owner_id == FeatureId) != (Value.id in BoundParams) for Value in Values
    ):
        raise ValueError(
            "ordinary revolve has another unresolved neutral parameter owner"
        )
    return (
        tuple(BoundParams.get(Value.id, Value) for Value in Values)
        + tuple(Value for Value in BoundParams.values() if Value.id not in Existing),
        tuple(BoundParams),
    )
