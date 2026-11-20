from convert.adapters.solidworks.Assembly.Display.DisplayOwner import DisplayOwner


# typed visibility is optional so existing consumers keep the same raw display rows
def DisplayData(DisplayValue: DisplayOwner | None) -> dict[str, object]:
    if DisplayValue is None:
        return {}
    return {
        "typed_display_states": (
            {
                "configuration_object_id": DisplayValue.ConfigObjectId,
                "configuration_id": DisplayValue.ConfigId,
                "configuration_name": DisplayValue.ConfigName,
                "model_object_id": DisplayValue.ModelObjectId,
                "list_object_id": DisplayValue.ListObjectId,
                "state_object_id": DisplayValue.StateObjectId,
                "name": DisplayValue.StateName,
                "visibility": tuple(
                    {
                        "native_object_id": MemberValue.ObjectId,
                        "native_feature_id": MemberValue.FeatureId,
                        "visible": MemberValue.Visible,
                    }
                    for MemberValue in DisplayValue.MemberValues
                ),
            },
        ),
    }
