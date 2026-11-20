from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import (
    MakeBlindPartFromPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import (
    ProjectBlind,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from interchange.document.Models.DocumentModel import CadDocument


# the closed polygon profile uses the shared complete part construction with its own explicit topology admission
def MakePolygonPart(
    DocumentValue: CadDocument, InputValue: PartBuildInput
) -> PartCandidate:
    return MakeBlindPartFromPlan(
        DocumentValue, InputValue, ProjectBlind(DocumentValue, ReadLineLoop)
    )
