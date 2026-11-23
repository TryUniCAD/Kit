from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanOriginBox import (
    PlanOriginBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepareBoxAxes import (
    PrepareBoxAxes,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.ProjectBoxAxes import (
    ProjectBoxAxes,
)
from interchange.document.Models.DocumentModel import CadDocument


# the original box and its selectable origin axes must derive from the same strict source archive
def PrepOrigAxes(DocumentValue: CadDocument, PathValue: str) -> PartCandidate:
    PlanValue = PlanOriginBox(DocumentValue)
    SourceValue = PlanValue.PartSource
    AxesValue = ProjectBoxAxes(PlanValue.SourceDatums.AxisValue)
    return PrepareBoxAxes(
        SourceValue.ModelValue,
        PathValue,
        SourceValue.CreationEpoch,
        SourceValue.PropertiesValue,
        AxesValue,
        TopAttached=False,
        UnitsValue=SourceValue.UnitsValue,
    )
