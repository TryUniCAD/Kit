from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.BodyNames.PlainBodyView import (
    PlainBodyView,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyLabel import (
    ReadBodyLabel,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from convert.adapters.solidworks.Core.Preparation.ReadCornerAnchor import (
    ReadCornerRef,
)
from interchange.document.Models.DocumentModel import CadDocument


# the signed rectangle must prove its actual origin anchor and principal support before the constructor can lower either
def PlanTopCorner(DocumentValue: CadDocument) -> tuple[CadDocument, BlindPlan] | None:
    if (
        len(DocumentValue.support_planes) != 1
        or DocumentValue.support_planes[0].name != "Top Plane"
        or len(DocumentValue.parameters) != 3
        or len(DocumentValue.sketches) != 1
    ):
        return None
    (SketchValue,) = DocumentValue.sketches
    if (
        len(SketchValue.closed_profile_entity_ids) != 1
        or len(SketchValue.closed_profile_entity_ids[0]) != 4
    ):
        return None
    CheckPlainScope(DocumentValue)
    if DocumentValue.units != "mm" or not DocumentValue.capabilities <= KPartWriteCaps:
        raise ValueError(
            "anchored Top rectangle requires the qualified neutral profile"
        )
    _ = ReadBodyLabel(DocumentValue)
    Projected = ReplaceValue(DocumentValue, sketches=(ReadCornerRef(SketchValue),))
    return Projected, ProjectRectDims(PlainBodyView(Projected), TopAttached=True)
