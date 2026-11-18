from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner


# dimensional provenance retains its actual end slot and distinguishes the termination from physical direction
def ReportEndFields(OwnerValue: ExtrudeOwner) -> dict[str, object]:
    DepthValue = OwnerValue.DepthValue.DepthValue
    Result: dict[str, object] = {
        "parameter_name": DepthValue.name,
        "depth_m": DepthValue.native_value,
        "parameter_owner": DepthValue.TypedOwner,
        "end_condition": OwnerValue.ModeValue.value,
        "reversed": OwnerValue.IsReversed,
    }
    if OwnerValue.SecondValue is not None:
        SecondValue = OwnerValue.SecondValue.DepthValue
        Result.update(
            second_parameter_name=SecondValue.name,
            second_depth_m=SecondValue.native_value,
            second_parameter_owner=SecondValue.TypedOwner,
        )
    return Result
