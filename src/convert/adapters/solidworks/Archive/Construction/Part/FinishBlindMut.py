from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughPartSpec import (
    ThroughPartSpec,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThruCutPart import (
    MakeThruCutPart,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import (
    MakeBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import (
    EmitPartStreams,
)
from convert.adapters.solidworks.Archive.Construction.Part.Equations.BindWidthMut import (
    BindWidthMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartCutMut import (
    MakePartCutMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PartPlan import (
    KPartPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PocketPlan import (
    PocketPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt


# plain and constrained profiles must share the same remaining boss allocation headers linked serializers and complete container construction
def FinishBlindMut(
    SystemValue: PartSystem,
    ProfileValue: ProfileGraph,
    InputValue: PartBuildInput,
    PlanValue: KPartPlan,
    Allocator: PersistentIds,
    SketchDims: tuple[KeywordDim, ...] = (),
    *,
    PocketValue: PocketPlan | None = None,
    ThroughValue: ThroughPartSpec | None = None,
    WidthDriver: DimensionGraph | None = None,
) -> PartCandidate:
    EndInput: BlindEndInput | BossEndInput
    if ThroughValue is not None:
        if PocketValue is not None or ThroughValue.StockValue is not PlanValue:
            raise ValueError(
                "through all composition requires its actual sole stock plan"
            )
        EndInput = BossEndInput(PlanValue.DepthValue, False, 19000, "mid_plane")
    elif isinstance(PlanValue, CirclePlan):
        EndInput = PlanValue.EndValue
    elif isinstance(PlanValue, BlindPlan) and PlanValue.Reversed:
        EndInput = BossEndInput(
            PlanValue.DepthValue, True, 19000, "blind", DepthName=PlanValue.DepthName
        )
    else:
        EndInput = BlindEndInput(
            PlanValue.DepthValue, False, 19000, PlanValue.DepthName
        )
    BossValue = MakeBlindMut(
        PlanValue.FeatureName,
        SystemValue.RootValue,
        ProfileValue,
        EndInput,
        InputValue.TargetValue,
        Allocator,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
    )
    if WidthDriver is not None:
        BindWidthMut(SystemValue.RootValue, WidthDriver, BossValue.DimensionsValue[0])
    CutValue: CutGraph | None = None
    CutSketchDims: tuple[KeywordDim, ...] = ()
    if PocketValue is not None:
        CutValue, CutSketchDims = MakePartCutMut(
            SystemValue, InputValue, PocketValue, Allocator
        )
    if ThroughValue is not None:
        CutValue = MakeThruCutPart(SystemValue, InputValue, ThroughValue, Allocator)
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    HeadersValue = MakePartHeaders(SystemValue, InputValue, Allocator)
    DefinitionValue = MakePartDef(InputValue.DefinitionValue, InputValue.DensityValue)
    FeatureValues = (
        *SystemValue.FeatureValues,
        ProfileValue.ProfileValue,
        BossValue.FeatureValue,
    )
    if CutValue is not None:
        FeatureValues += (CutValue.ProfileValue.ProfileValue, CutValue.FeatureValue)
    StreamsValue, ConfigValue, ResolvedValue = EmitPartStreams(
        SystemValue,
        FeatureValues,
        HeadersValue,
        DefinitionValue,
        InputValue,
        PlanValue,
        SketchDims,
        CutValue=CutValue,
        CutSketchDims=CutSketchDims,
        PartRelations=WidthDriver is not None,
    )
    BytesValue = BuildSldprt(StreamsValue, FormatVersion=4)
    return PartCandidate(
        SystemValue,
        ProfileValue,
        BossValue,
        HeadersValue[0],
        HeadersValue[1],
        HeadersValue[2],
        DefinitionValue,
        ConfigValue,
        ResolvedValue,
        StreamsValue,
        BytesValue,
        PlanValue,
        CutValue,
    )
