from collections.abc import Mapping
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)
from interchange.assembly.ComponentInstance import ComponentInst


# only completely admitted typed mate graphs may replace legacy anchor defaults while deferred and unsupported reads retain their prior behavior
def WithTypedFixed(
    Instances: tuple[ComponentInst, ...], ReportValue: Mapping[str, object] | None
) -> tuple[ComponentInst, ...]:
    if ReportValue is None or ReportValue.get("status") != "admitted":
        return Instances
    if ReportValue.get("full_selected_mate_graph") is not True:
        raise ValueError("fixed flags require fully admitted typed mate semantics")
    RowsValue = ReadRows(ReportValue["occurrence_fixed_flags"])
    if any(type(RowValue["fixed"]) is not bool for RowValue in RowsValue):
        raise ValueError("typed fixed flags require actual boolean values")
    FlagsValue = {
        FieldInt(RowValue, "native_feature_id"): CastValue(bool, RowValue["fixed"])
        for RowValue in RowsValue
    }
    FeatureIds = tuple(
        FieldInt(ItemValue.attributes, "native_feature_id") for ItemValue in Instances
    )
    if (
        len(FlagsValue) != len(RowsValue)
        or len(set(FeatureIds)) != len(FeatureIds)
        or set(FlagsValue) != set(FeatureIds)
    ):
        raise ValueError("typed anchor flags and actual public instances differ")
    return tuple(
        ReplaceValue(ItemValue, fixed=FlagsValue[FeatureId])
        for ItemValue, FeatureId in zip(Instances, FeatureIds, strict=True)
    )
