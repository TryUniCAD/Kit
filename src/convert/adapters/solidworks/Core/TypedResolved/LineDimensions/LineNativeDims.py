from convert.adapters.solidworks.Core.Native import NativeDimension
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDims import (
    LineDims,
)


# normal parameter projection must consume the retained live scalar and preserve actual archive ownership metadata
def LineNativeDims(DimsValue: LineDims | None) -> tuple[NativeDimension, ...]:
    if DimsValue is None:
        return ()
    return tuple(
        NativeDimension(
            Driver.NameValue,
            Driver.MetresValue / 0.001,
            "length",
            f"{Driver.MetresValue / 0.001:.17g}mm",
            native_value=Driver.MetresValue,
            native_role="driving",
            TypedOwner={
                **Driver.ParamOwner,
                "value_field": "f58",
                "dimension_id": Driver.NodeValue.FieldsValue["f50"],
                "dimension_index": Driver.NodeValue.IndexValue,
                "display_index": Driver.DisplayValue.IndexValue,
                "handle_index": Driver.HandleValue.IndexValue,
                "group_index": Driver.IndexValue,
            },
        )
        for Driver in DimsValue.DriverValues
    )
