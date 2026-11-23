from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.FinishNamedPart import (
    FinishNamedPart,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.NameOutputMut import (
    NameOutputMut,
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
from convert.adapters.solidworks.Archive.Construction.Part.Materials.BindPartMatMut import (
    BindPartMatMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.Materials.PartMatIntent import (
    PartMatIntent,
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
    AllocatorValue: PersistentIds | None = None,
    MaterialValue: PartMatIntent | None = None,
    DormantDepth: float | None = None,
    BodyName: str | None = None,
) -> PartCandidate:
    if (DormantDepth is not None or BodyName is not None) and (
        not WidthDepth or AnchorValue.KindValue != "corner" or PlanValue.Reversed
    ):
        raise ValueError(
            "anchored output owners require an actual forward corner equation"
        )
    if BodyName is not None and (
        type(BodyName) is not str
        or not 1 <= len(BodyName) <= 255
        or not BodyName.isascii()
        or not BodyName.isprintable()
        or BodyName != BodyName.strip()
    ):
        raise ValueError("named corner equation requires a valid ASCII body label")
    Allocator = PersistentIds() if AllocatorValue is None else AllocatorValue
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
    if MaterialValue is not None:
        BindPartMatMut(SystemValue, MaterialValue)
    SketchDims = MakeSketchKeys(Dimensions, InputValue.DocumentUnits.LengthUnit)
    CandidateValue = FinishBlindMut(
        SystemValue,
        ProfileValue,
        InputValue,
        PlanValue,
        Allocator,
        SketchDims,
        WidthDriver=Dimensions[0] if WidthDepth else None,
        DormantDepth=DormantDepth,
    )
    if BodyName is None or BodyName == PlanValue.FeatureName:
        return CandidateValue
    _ = NameOutputMut(CandidateValue, BodyName)
    return FinishNamedPart(
        CandidateValue, InputValue, SketchDims, PartRelations=WidthDepth
    )
