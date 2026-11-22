from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Part.Equations.PlanWidthDepth import (
    PlanWidthDepth,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.ReadCornerAnchor import (
    ReadCornerRef,
)
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.Enums.EnumDocument import Capability
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid


# the neutral anchor and dependency must both pass their actual owner checks before the common rectangle projection
def PlanEqPart(DocumentValue: CadDocument) -> tuple[CadDocument, BlindPlan]:
    CheckPlainScope(DocumentValue)
    if len(
        DocumentValue.sketches
    ) != 1 or not DocumentValue.capabilities <= KPartWriteCaps | {
        Capability.KExpressions
    }:
        raise ValueError("local equation preparation requires a supported part model")
    AssertValid(DocumentValue)
    SketchValue = ReadCornerRef(DocumentValue.sketches[0])
    Projected = ReplaceValue(DocumentValue, sketches=(SketchValue,))
    return Projected, PlanWidthDepth(Projected)
