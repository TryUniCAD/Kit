from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadRectPlace import (
    ReadRectPlace,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Children.SketchLabelIn import (
    KSketchLabels,
    SketchLabelIn,
)
from interchange.document.Models.DocumentModel import CadDocument


# neutral driver ids must determine display roles before the child graph is generated
def BindRectLabels(
    ChildValue: CadDocument,
    PlanValue: BlindPlan,
    DefaultValue: RectDimInput,
    LabelValues: KSketchLabels,
) -> RectDimInput:
    if (
        PlanValue.AxisValue != "z"
        or PlanValue.Reversed
        or len(ChildValue.sketches) != 1
    ):
        raise ValueError("sketch label intent requires the canonical Front rectangle")
    RowsValue = CastValue(tuple[object, ...], LabelValues)
    if (
        type(CastValue(object, RowsValue)) is not tuple
        or len(RowsValue) != 2
        or any(type(RowValue) is not SketchLabelIn for RowValue in RowsValue)
    ):
        raise TypeError("rectangle requires two typed sketch labels")
    SketchValue = ChildValue.sketches[0]
    DriversValue = SketchValue.parameter_ids
    Indexed = {RowValue.ParameterId: RowValue for RowValue in LabelValues}
    if (
        SketchValue.id != PlanValue.SketchId
        or any(RowValue.SketchId != SketchValue.id for RowValue in LabelValues)
        or len(Indexed) != 2
        or set(Indexed) != set(DriversValue)
    ):
        raise ValueError("rectangle labels require both actual owned sketch drivers")
    Width, Height = (Indexed[IdentityValue] for IdentityValue in DriversValue)
    _ = ReadRectPlace(
        PlanValue.VerticesValue, 0, (0, 1), PlanValue.WidthValue, Width.TextPoint[:2]
    )
    _ = ReadRectPlace(
        PlanValue.VerticesValue, 1, (1, 2), PlanValue.HeightValue, Height.TextPoint[:2]
    )
    return ReplaceValue(
        DefaultValue,
        WidthText=Width.TextPoint[:2],
        HeightText=Height.TextPoint[:2],
        TextDepths=(Width.TextPoint[2], Height.TextPoint[2]),
        RouteCenter=(Width.RouteCenter, Height.RouteCenter),
    )
