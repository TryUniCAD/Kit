from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.CheckAnchorSpec import (
    CheckAnchorSpec,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeAnchorPart import (
    MakeAnchorPart,
)
from interchange.document.Models.DocumentModel import CadDocument


# named anchored outputs need actual origin relations and construction geometry before the common extrusion consumes the owned profile
def MakeAnchorBase(
    DocumentValue: CadDocument,
    InputValue: PartBuildInput,
    AnchorValue: AnchorPartInput,
) -> PartCandidate:
    CheckAnchorSpec(AnchorValue)
    PlanValue = ProjectRectDims(DocumentValue, TopAttached=AnchorValue.TopAttached)
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    return MakeAnchorPart(InputValue, PlanValue, AnchorValue)
