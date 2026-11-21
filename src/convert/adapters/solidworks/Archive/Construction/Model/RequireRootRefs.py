from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Model.PartRootRefs import (
    PartRootRefs,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)


# explicit dependency validation keeps incomplete style or unit ownership from masquerading as a complete root graph
def RequireRootRefs(RefsValue: PartRootRefs) -> None:
    if type(CastValue(object, RefsValue)) is not PartRootRefs or not isinstance(
        CastValue(object, RefsValue.DetailFields), MutableMapping
    ):
        raise TypeError("part root requires typed generated dependency bindings")
    StandardValue = RefsValue.DetailFields.get("f10")
    if type(StandardValue) is not int or StandardValue != 1:
        raise ValueError(
            "part root currently requires classified effective detail standard one"
        )
    RequireRootNode(RefsValue.DocumentUnits, "moUnitsTable_c")
    RequireRootNode(RefsValue.AnalysisUnits, "moUnitsTable_c")
    if RefsValue.DocumentUnits is RefsValue.AnalysisUnits:
        raise ValueError("fresh document and analysis units require distinct owners")
    RequireRootNode(RefsValue.VisualValue, "moVisualProperties_c")
    if RefsValue.VisualValue.FieldsValue.get("f5c") != 1:
        raise ValueError("part visual dependency must select its explicit model state")
    if (
        type(CastValue(object, RefsValue.ViewValues)) is not tuple
        or len(RefsValue.ViewValues) != 10
        or len({id(NodeValue) for NodeValue in RefsValue.ViewValues}) != 10
    ):
        raise ValueError(
            "part root requires ten independently owned ordinary view nodes"
        )
    for IndexValue, NodeValue in enumerate(RefsValue.ViewValues):
        RequireRootNode(NodeValue, "moView_c")
        if NodeValue.FieldsValue.get("f360") != IndexValue:
            raise ValueError(
                "part root view order differs from its native indexed vocabulary"
            )
