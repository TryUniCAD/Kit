from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import (
    FinishBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import (
    MakePartProfMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
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
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import (
    MakeRectDimsMut,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from interchange.document.Models.DocumentModel import CadDocument


# a neutral dimensioned rectangle must allocate its real sketch drivers before the common boss composer consumes later feature identities
def MakeRectDimPart(
    DocumentValue: CadDocument, InputValue: PartBuildInput, DimensionInput: RectDimInput
) -> PartCandidate:
    PlanValue = ProjectRectDims(DocumentValue)
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(InputValue, PlanValue, Allocator)
    ProfileValue = MakePartProfMut(SystemValue, InputValue, PlanValue, Allocator)
    Dimensions = MakeRectDimsMut(ProfileValue, DimensionInput, Allocator)
    return FinishBlindMut(
        SystemValue,
        ProfileValue,
        InputValue,
        PlanValue,
        Allocator,
        MakeSketchKeys(Dimensions, InputValue.DocumentUnits.LengthUnit),
    )
