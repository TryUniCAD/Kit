from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxes import (
    PrismAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxis import (
    PrismAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Patterns.MakeTiltPick import (
    MakeTiltPick,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Features.FeatureStep import FeatureStep
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.VectorSpace import SpaceVector


# both selected parents become real owned neutral selections and the endpoints retain their archive source
def BindOneAxis(
    LinkValue: NativeLink, AxisValue: PrismAxis, StepValue: FeatureStep
) -> tuple[FeatureStep, tuple[Selection, Selection]]:
    First, Second = (
        MakeTiltPick(
            LinkValue,
            AxisValue.NodeValue,
            PickValue.PlaneValue,
            PickValue.WrapperValue,
            RoleName,
            True,
        )
        for PickValue, RoleName in zip(
            AxisValue.PicksValue, ("axis-first-plane", "axis-second-plane"), strict=True
        )
    )
    Definition = PlaneAxis(
        First.id,
        Second.id,
        SpaceVector(*(Value * 1000 for Value in AxisValue.StartValue)),
        SpaceVector(*(Value * 1000 for Value in AxisValue.EndValue)),
    )
    if StepValue.name != ReadNativeName(AxisValue.NodeValue) or StepValue.suppressed:
        raise ValueError("neutral origin axis lost its actual name or active state")
    return ReplaceValue(
        StepValue,
        definition=Definition,
        input_feature_ids=tuple(
            f"sldprt:feature:{NativeNodeId(PickValue.PlaneValue)}"
            for PickValue in AxisValue.PicksValue
        ),
        selection_ids=(First.id, Second.id),
        provenance=TypedProvenance(
            NativeNodeSpan(LinkValue, AxisValue.NodeValue), StepValue.id
        ),
        attributes=FreezeMapping(
            {
                **StepValue.attributes,
                "solidworks.native_axis_data": NativeNodeSpan(
                    LinkValue, AxisValue.DataValue
                ),
                "solidworks.native_axis_hidden": False,
            }
        ),
    ), (First, Second)


# exact native root order and complete axis ownership survive the ordinary document projection
def BindPrismAxes(Document: CadDocument, AxesValue: PrismAxes | None) -> CadDocument:
    if AxesValue is None:
        return Document
    LinkValue = AxesValue.LinkValue
    OrderValue = tuple(f"sldprt:feature:{Value}" for Value in IndexFeatures(LinkValue))
    Features = {StepValue.id: StepValue for StepValue in Document.feature_timeline}
    if set(OrderValue) != set(Features) or len(Features) != len(
        Document.feature_timeline
    ):
        raise ValueError(
            "neutral origin axis projection lacks the actual root inventory"
        )
    PicksValue = list(Document.selections)
    for AxisValue in AxesValue.AxesValue:
        KeyValue = f"sldprt:feature:{NativeNodeId(AxisValue.NodeValue)}"
        BoundValue, Additional = BindOneAxis(LinkValue, AxisValue, Features[KeyValue])
        Features[KeyValue] = BoundValue
        PicksValue.extend(Additional)
    return ReplaceValue(
        Document,
        selections=tuple(PicksValue),
        feature_timeline=tuple(
            ReplaceValue(Features[KeyValue], order=Ordinal)
            for Ordinal, KeyValue in enumerate(OrderValue)
        ),
    )
