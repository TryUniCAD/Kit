from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.CheckAnchorSpec import (
    CheckAnchorSpec,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.FinishBlindMut import (
    FinishBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import (
    MakePartProfMut,
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
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import (
    MakeCornerMut,
)
from convert.adapters.solidworks.Archive.Construction.RectangleCenters.MakeCenterMut import (
    MakeCenterMut,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import (
    MakeRectDimsMut,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
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
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(InputValue, PlanValue, Allocator)
    ProfileValue = MakePartProfMut(SystemValue, InputValue, PlanValue, Allocator)
    Dimensions = MakeRectDimsMut(
        ProfileValue,
        AnchorValue.DimensionsValue,
        Allocator,
        PlanValue.SketchDriverNames,
    )
    if AnchorValue.KindValue == "corner":
        _ = MakeCornerMut(ProfileValue, SystemValue.OriginValue)
    else:
        _ = MakeCenterMut(ProfileValue, SystemValue.OriginValue)
    return FinishBlindMut(
        SystemValue,
        ProfileValue,
        InputValue,
        PlanValue,
        Allocator,
        MakeSketchKeys(Dimensions, InputValue.DocumentUnits.LengthUnit),
    )
