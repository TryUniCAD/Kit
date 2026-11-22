from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import (
    ProjectRevolve,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.Features.Revolves.ThinRevolve import ThinRevolve


# typed thin intent selects its own writer before generic part publication
def HasThinWrite(DocumentValue: CadDocument) -> bool:
    return any(
        isinstance(FeatureValue.definition, ThinRevolve)
        for FeatureValue in DocumentValue.feature_timeline
    )


# internal preparation binds the thin profile owners with the shared revolve grammar
def PlanThinPart(DocumentValue: CadDocument) -> RevolvePlan | None:
    if not HasThinWrite(DocumentValue):
        return None
    return ProjectRevolve(DocumentValue)


# the measured writer admits authored model domains covered by its complete neutral recipe
def PlanThinWrite(DocumentValue: CadDocument) -> RevolvePlan:
    CheckPlainScope(DocumentValue)
    if not GetDocumentCaps(DocumentValue) <= KPartWriteCaps | {Capability.KSelections}:
        raise ValueError("measured thin revolve has unrepresented capabilities")
    PlanValue = PlanThinPart(DocumentValue)
    if PlanValue is None:
        raise ValueError("measured thin revolve requires one portable authored feature")
    return PlanValue
