from typing import Mapping as TypeMap, cast as CastValue

from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.SupportPlane import SupportPlane


# both plane axis forms resolve the original ordered local support owners
def ReadAxisPlanes(
    StepValue: FeatureStep,
    PickIds: tuple[str, str],
    Selections: TypeMap[str, Selection],
    Frames: TypeMap[str, SupportPlane],
) -> tuple[SupportPlane, SupportPlane]:
    if StepValue.selection_ids != PickIds:
        raise ValueError("has inconsistent ordered selection roles")
    Planes: list[SupportPlane] = []
    for PickId in PickIds:
        Selected = Selections.get(PickId)
        if (
            Selected is None
            or not isinstance(CastValue(object, Selected.path), tuple)
            or len(Selected.path) != 1
        ):
            raise ValueError("requires a direct support plane selection")
        (Element,) = Selected.path
        if (
            not isinstance(CastValue(object, Element), SelectPathElem)
            or Element.entity_kind != "support_plane"
            or Element.subelement != ""
            or not isinstance(CastValue(object, Element.entity_id), str)
            or not Element.entity_id.strip()
        ):
            raise ValueError("requires a direct support plane selection")
        PlaneValue = Frames.get(Element.entity_id)
        if PlaneValue is None:
            raise ValueError("selects a missing support plane")
        Planes.append(PlaneValue)
    FirstPlane, SecondPlane = Planes
    if FirstPlane.id == SecondPlane.id:
        raise ValueError("must select two distinct support planes")
    return FirstPlane, SecondPlane
