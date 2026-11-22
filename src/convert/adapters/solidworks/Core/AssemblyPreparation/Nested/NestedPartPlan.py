from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from interchange.document.Models.DocumentModel import CadDocument


# each nested leaf retains its actual validated document and neutral rectangular boss plan
@Dataclass(frozen=True, slots=True)
class NestedPartPlan:
    DocumentValue: CadDocument
    PartValue: BlindPlan
