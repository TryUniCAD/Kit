from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
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
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import (
    EmitPartStreams,
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
) -> PartCandidate:
    EndInput = (
        PlanValue.EndValue
        if isinstance(PlanValue, CirclePlan)
        else BlindEndInput(PlanValue.DepthValue, False, 19000, PlanValue.DepthName)
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
    CutValue: CutGraph | None = None
    CutSketchDims: tuple[KeywordDim, ...] = ()
    if PocketValue is not None:
        CutValue, CutSketchDims = MakePartCutMut(
            SystemValue, InputValue, PocketValue, Allocator
        )
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
