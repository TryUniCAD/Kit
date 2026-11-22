from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveAngle import (
    RevolveAngle,
)


# independent end controls cannot share a display handle dimension or parameter
def CheckRevPair(AlongValue: RevolveAngle, AgainstValue: RevolveAngle) -> None:
    if (
        AgainstValue.NameValue != "D2"
        or AlongValue.DisplayValue is AgainstValue.DisplayValue
        or AlongValue.HandleValue is AgainstValue.HandleValue
        or AlongValue.ParameterValue is AgainstValue.ParameterValue
        or AlongValue.DimensionValue.FieldsValue["f50"]
        == AgainstValue.DimensionValue.FieldsValue["f50"]
    ):
        raise ValueError("ordinary revolve requires its distinct D1 and D2 owners")
