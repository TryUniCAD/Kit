from typing import Mapping as TypeMap, cast as CastValue

from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.CheckAxisFit import CheckAxisFit
from interchange.Features.FeaturePlaneAxis import PlaneAxis
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.SupportPlane import SupportPlane


# only the owning feature can identify the actual ordered plane selections in its document
def GetAxisErrors(
    StepValue: FeatureStep,
    Definition: PlaneAxis,
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
) -> tuple[str, ...]:
    PrefixValue = f"plane axis {StepValue.id}"
    PickIds = (Definition.FirstPlaneSelectionId, Definition.SecondPlaneSelectionId)
    if (
        StepValue.kind != FeatureKind.KReference
        or StepValue.sketch_id is not None
        or StepValue.operation is not None
        or StepValue.parameter_ids
    ):
        return (
            f"{PrefixValue} requires a reference feature with only plane selections",
        )
    if StepValue.selection_ids != PickIds:
        return (f"{PrefixValue} has inconsistent ordered selection roles",)
    Planes: list[SupportPlane] = []
    for PickId in PickIds:
        Selected = Selections.get(PickId)
        if (
            Selected is None
            or not isinstance(CastValue(object, Selected.path), tuple)
            or len(Selected.path) != 1
        ):
            return (f"{PrefixValue} requires a direct support plane selection",)
        (Element,) = Selected.path
        if (
            not isinstance(CastValue(object, Element), SelectPathElem)
            or Element.entity_kind != "support_plane"
            or Element.subelement != ""
            or not isinstance(CastValue(object, Element.entity_id), str)
            or not Element.entity_id.strip()
        ):
            return (f"{PrefixValue} requires a direct support plane selection",)
        PlaneValue = Frames.get(Element.entity_id)
        if PlaneValue is None:
            return (f"{PrefixValue} selects a missing support plane",)
        Planes.append(PlaneValue)
    FirstPlane, SecondPlane = Planes
    if FirstPlane.id == SecondPlane.id:
        return (f"{PrefixValue} must select two distinct support planes",)
    try:
        CheckAxisFit(Definition, FirstPlane.transform, SecondPlane.transform)
    except (ValueError, OverflowError) as ErrorInfo:
        return (f"{PrefixValue} geometry is invalid: {ErrorInfo}",)
    return ()
