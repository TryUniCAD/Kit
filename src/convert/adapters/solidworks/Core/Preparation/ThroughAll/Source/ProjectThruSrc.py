from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.CheckSourceEnv import (
    CheckSourceEnv,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ListSourceGaps import (
    ListSourceGaps,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ProjectSrcShape import (
    ProjectSrcShape,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ThruSourceEnv import (
    ThruSourceEnv,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ThruSourcePlan import (
    ThruSourcePlan,
)
from interchange.document.Models.DocumentModel import CadDocument


# the full source and its explicit missing fields must remain attached to every executable geometry projection
def ProjectThruSrc(DocumentValue: CadDocument, OutputName: str) -> ThruSourcePlan:
    CheckSourceEnv(DocumentValue)
    return ThruSourcePlan(
        ProjectSrcShape(DocumentValue, OutputName),
        ThruSourceEnv(DocumentValue, ListSourceGaps(DocumentValue)),
    )
