from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Equations.PlanWidthDepth import (
    PlanWidthDepth,
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
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import (
    MakeCornerMut,
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


# the anchored equation binds actual sketch and boss dimension owners through the ordinary part builder
def MakeDerivedBoss(
    DocumentValue: CadDocument, InputValue: PartBuildInput, AnchorValue: RectDimInput
) -> PartCandidate:
    PlanValue = PlanWidthDepth(DocumentValue)
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(InputValue, PlanValue, Allocator)
    ProfileValue = MakePartProfMut(SystemValue, InputValue, PlanValue, Allocator)
    Dimensions = MakeRectDimsMut(ProfileValue, AnchorValue, Allocator)
    _ = MakeCornerMut(ProfileValue, SystemValue.OriginValue)
    return FinishBlindMut(
        SystemValue,
        ProfileValue,
        InputValue,
        PlanValue,
        Allocator,
        MakeSketchKeys(Dimensions, InputValue.DocumentUnits.LengthUnit),
        WidthDriver=Dimensions[0],
    )
