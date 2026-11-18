from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import (
    MakeBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import (
    EmitPartStreams,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import (
    ProjectPlain,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Profile.MakeProfileMut import (
    MakeProfileMut,
)
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import (
    PolygonInput,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from interchange.document.Models.DocumentModel import CadDocument


# the first complete donor free sdk candidate must synthesize every native stream from the actual neutral graph and explicit construction settings
def MakeBlindPart(
    DocumentValue: CadDocument, InputValue: PartBuildInput
) -> PartCandidate:
    return MakeBlindPartFromPlan(DocumentValue, InputValue, ProjectPlain(DocumentValue))


# an admitted closed profile must use the same graph allocation linked stream writers and container path
def MakeBlindPartFromPlan(
    DocumentValue: CadDocument, InputValue: PartBuildInput, PlanValue: BlindPlan
) -> PartCandidate:
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    Allocator = PersistentIds()
    SystemValue = MakePartBaseMut(InputValue, PlanValue, Allocator)
    ProfileValue = MakeProfileMut(
        PlanValue.SketchName,
        SystemValue.RootValue,
        SystemValue.SystemValues.PlaneValues["z"],
        "z",
        PolygonInput(PlanValue.VerticesValue, 19000),
        InputValue.TargetValue,
        Allocator,
    )
    BossValue = MakeBlindMut(
        PlanValue.FeatureName,
        SystemValue.RootValue,
        ProfileValue,
        BlindEndInput(PlanValue.DepthValue, False, 19000),
        InputValue.TargetValue,
        Allocator,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
    )
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    HeadersValue = MakePartHeaders(SystemValue, InputValue, Allocator)
    DefinitionValue = MakePartDef(InputValue.DefinitionValue, InputValue.DensityValue)
    FeatureValues = (
        *SystemValue.FeatureValues,
        ProfileValue.ProfileValue,
        BossValue.FeatureValue,
    )
    StreamsValue, ConfigValue, ResolvedValue = EmitPartStreams(
        SystemValue, FeatureValues, HeadersValue, DefinitionValue, InputValue, PlanValue
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
    )
