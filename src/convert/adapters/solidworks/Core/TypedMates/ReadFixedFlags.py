from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Core.TypedMates.IsAnchorFixed import IsAnchorFixed


# selected mate semantics must retain the independently serialized anchor flag rather than infer fixed state from solve status or xml presence
def ReadFixedFlags(Context: PlanarContext) -> tuple[dict[str, object], ...]:
    BodyValue = RequireRecord(Context.ModelNode.FieldsValue["f68"])
    ListValue = RequireRecord(BodyValue["list"])
    References = tuple(
        RequireNode(RowValue["o"], "moReference_c")
        for RowValue in ReadRows(ListValue["items"])
    )
    FeatureIds = tuple(
        FieldInt(NodeValue.FieldsValue, "f08") for NodeValue in References
    )
    if len(set(FeatureIds)) != len(FeatureIds) or set(FeatureIds) != set(
        Context.OccurrenceMap
    ):
        raise ValueError(
            "typed fixed flags require the complete ordinary occurrence set"
        )
    ResultValue: list[dict[str, object]] = []
    for NodeValue, FeatureId in zip(References, FeatureIds, strict=True):
        ItemValue = Context.OccurrenceMap[FeatureId]
        ResultValue.append(
            {
                "native_feature_id": FeatureId,
                "fixed": IsAnchorFixed(
                    NodeValue, f"{ItemValue.name}-{ItemValue.reference_number}"
                ),
            }
        )
    return tuple(ResultValue)
