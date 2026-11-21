from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
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
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
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


# both anchored rectangle routes need the live sketch handles before finishing the common part archive
def MakeAnchorPart(
    InputValue: PartBuildInput,
    PlanValue: BlindPlan,
    AnchorValue: AnchorPartInput,
    *,
    WidthDepth: bool = False,
) -> PartCandidate:
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
        WidthDriver=Dimensions[0] if WidthDepth else None,
    )
