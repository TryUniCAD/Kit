from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import (
    ProjectBlind,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument


# the ordinary native profile must admit only the proven millimetre line loop and front support semantics
def PlanPartWrite(DocumentValue: CadDocument) -> BlindPlan:
    CheckPlainScope(DocumentValue)
    if not DocumentValue.capabilities <= KPartWriteCaps:
        raise ValueError("native part preparation has unrepresented capabilities")
    PlanValue = ProjectBlind(DocumentValue, ReadLineLoop)
    if DocumentValue.units != "mm" or PlanValue.PlaneName != "Front Plane":
        raise ValueError("native part preparation requires millimetres and Front Plane")
    return PlanValue
