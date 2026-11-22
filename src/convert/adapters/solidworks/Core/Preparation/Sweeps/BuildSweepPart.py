from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.Materials.MakePartDensity import (
    MakePartDensity,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Ghost.MakeGhostPair import (
    MakeGhostPair,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.MakeSweepData import (
    MakeSweepData,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.MakeSweepKeys import (
    MakeSweepKeys,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.MakeSweepNode import (
    MakeSweepNode,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Refs.MakeSwCurve import (
    MakeSwCurve,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Scene.BindSwSceneMut import (
    BindSwSceneMut,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.MakeSwProfMut import (
    MakeSwProfMut,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.SweepProfiles import (
    SweepProfiles,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepLabels import (
    SweepLabels,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepPart import SweepPart
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KGhostPartition
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent


# the typed section and path must survive neutral sketch projection with both independent driver values intact
def CheckSweepDims(ProfilesValue: SweepProfiles, IntentValue: SweepIntent) -> None:
    Diameter = RequireScalar(
        ProfilesValue.DiameterValue.ParameterValue.FieldsValue["f58"]
    )
    Radius = RequireScalar(ProfilesValue.RadiusValue.ParameterValue.FieldsValue["f58"])
    if (Diameter / 2, Radius) != (
        IntentValue.SectionValue.Radius,
        IntentValue.PathValue.Radius,
    ):
        raise ValueError("sweep profiles must preserve both actual independent drivers")


# the isolated standard sweep composer builds its linked archive entirely from model intent and actual derived owners
def BuildSweepPart(IntentValue: SweepIntent) -> SweepPart:
    if type(IntentValue) is not SweepIntent:
        raise ValueError("sweep construction requires typed canonical neutral intent")
    LabelsValue = SweepLabels(IntentValue.NameValue)
    InputValue = ReplaceValue(
        MakePartRecipe(LabelsValue, IntentValue.OutputValue.SavedAt),
        DensityValue=IntentValue.DensityValue,
        OutputValue=IntentValue.OutputValue,
        PlatformViewMath=IntentValue.PlatformViewMath,
    )
    Allocator = PersistentIds()
    SystemValue = BindSwSceneMut(
        MakePartBaseMut(InputValue, LabelsValue, Allocator), InputValue, Allocator
    )
    PartValue = SystemValue.RootValue
    PartValue.FieldsValue["f1420"] = MakePartDensity(InputValue.DensityValue)
    ProfilesValue = MakeSwProfMut(
        SystemValue, InputValue, Allocator, IntentValue, LabelsValue
    )
    CheckSweepDims(ProfilesValue, IntentValue)
    SweepValue = MakeSweepNode(
        LabelsValue.FeatureName,
        PartValue,
        ProfilesValue,
        InputValue.TargetValue,
        Allocator,
    )
    PairValue = MakeGhostPair(PartValue, SweepValue, IntentValue)
    PartValue.FieldsValue["fd90"] = PairValue.ManagerValue
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    HeadersValue = MakePartHeaders(SystemValue, InputValue, Allocator)
    SectionValue = MakeSwCurve(
        SystemValue,
        HeadersValue[0],
        ProfilesValue.SectionValue,
        "x",
        PairValue.SectionId,
        ProfilesValue.DiameterValue,
    )
    PathValue = MakeSwCurve(
        SystemValue,
        HeadersValue[0],
        ProfilesValue.PathValue,
        "z",
        PairValue.PathId,
        ProfilesValue.RadiusValue,
    )
    SweepValue.FieldsValue["f820"] = MakeSweepData(SectionValue, PathValue)
    DefinitionValue = MakePartDef(InputValue.DefinitionValue, InputValue.DensityValue)
    KeywordsValue = MakeSweepKeys(
        LabelsValue.NameValue, SystemValue, ProfilesValue, SweepValue, InputValue
    )
    FeatureValues = (
        *SystemValue.FeatureValues,
        ProfilesValue.SectionValue,
        ProfilesValue.PathValue,
        SweepValue,
    )
    StreamsValue, ConfigValue, ResolvedValue = EmitPartArchive(
        SystemValue,
        FeatureValues,
        HeadersValue,
        DefinitionValue,
        InputValue,
        KeywordsValue,
        WriteSweeps=True,
    )
    StreamsValue[KGhostPartition] = PairValue.StreamValue
    return SweepPart(
        SystemValue,
        ProfilesValue,
        SweepValue,
        ConfigValue,
        ResolvedValue,
        StreamsValue,
        BuildSldprt(StreamsValue, FormatVersion=4),
    )
