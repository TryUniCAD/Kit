from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import (
    BindStockMut,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeBodyRef import (
    MakeBodyRef,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.MakeRevFeatMut import (
    MakeRevFeatMut,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.EmitRevStreams import (
    EmitRevStreams,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.RevolvePart import (
    RevolvePart,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.MakeSelectedRevRows import (
    MakeSelectedRevRows,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.ProjectSelectedRevolve import (
    ProjectSelectedRevolve,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Sketch.MakeRevProfMut import (
    MakeRevProfMut,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt
from interchange.document.Models.DocumentModel import CadDocument


# each stock allocates its active profile feature and live body before any downstream consumer
def MakeSelectedStock(
    System: PartSystem,
    InputValue: PartBuildInput,
    Plan: RevolvePlan,
    Allocator: PersistentIds,
    *,
    IsFirst: bool,
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode]:
    Profile, Axis = MakeRevProfMut(System, InputValue, Plan, Allocator)
    Feature, _, _, _ = MakeRevFeatMut(
        System, Profile, Axis, InputValue, Plan, Allocator
    )
    Feature.FieldsValue.update(f870=int(IsFirst), f544=1)
    Manager = CastValue(dict[str, object], System.RootValue.FieldsValue["fd88"])
    Atom = BindStockMut(Manager, Feature, AppendMember=True)
    return Profile.ProfileValue, Feature, Atom


# the complete selected stock part allocates two body atoms and the cut from the same neutral ownership graph
def MakeSelectedRevolvePart(
    DocumentValue: CadDocument, InputValue: PartBuildInput
) -> RevolvePart:
    Plan = ProjectSelectedRevolve(DocumentValue)
    First, Second, Cut = Plan.OperationsValue
    ExtraNames = (
        Second.SketchName,
        Second.FeatureName,
        Cut.SketchName,
        Cut.FeatureName,
    )
    CheckPartInput(DocumentValue, InputValue, First, ExtraNames)
    if (
        InputValue.PropertiesValue is not None
        or InputValue.DocumentUnits.AngleUnit != "degree"
    ):
        raise ValueError(
            "selected revolve construction requires ordinary degree presentation"
        )
    Allocator = PersistentIds()
    System = MakePartBaseMut(InputValue, First, Allocator)
    FirstProfile, FirstFeature, FirstAtom = MakeSelectedStock(
        System, InputValue, First, Allocator, IsFirst=True
    )
    SecondProfile, SecondFeature, SecondAtom = MakeSelectedStock(
        System, InputValue, Second, Allocator, IsFirst=False
    )
    Profile, Axis = MakeRevProfMut(System, InputValue, Cut, Allocator)
    Feature, Reference, End, Angle = MakeRevFeatMut(
        System, Profile, Axis, InputValue, Cut, Allocator, IsCut=True
    )
    Stock, Atom = ((FirstFeature, FirstAtom), (SecondFeature, SecondAtom))[
        Plan.SelectedIndex
    ]
    Wrapper = MakeBodyRef(System.RootValue, Stock, Atom)
    Wrapper.FieldsValue["f108"] = -1
    Feature.FieldsValue.update(
        f544=1, has_f548=1, f548={"n": 1, "items": [{"o": Wrapper}]}
    )
    SetCfgStampMut(System.ConfigValues[0], Allocator)
    Headers = MakePartHeaders(System, InputValue, Allocator)
    Definition = MakePartDef(InputValue.DefinitionValue, InputValue.DensityValue)
    Profiles = (FirstProfile, SecondProfile, Profile.ProfileValue)
    Features = (FirstFeature, SecondFeature, Feature)
    Roots = (
        *System.FeatureValues,
        FirstProfile,
        FirstFeature,
        SecondProfile,
        SecondFeature,
        Profile.ProfileValue,
        Feature,
    )
    KeyRows = MakeSelectedRevRows(
        System.FeatureValues, Profiles, Features, Plan.OperationsValue
    )
    Streams, Config, Resolved = EmitRevStreams(
        System, Roots, Headers, Definition, InputValue, Cut, KeyRowsValue=KeyRows
    )
    return RevolvePart(
        System,
        Profile,
        Feature,
        Reference,
        End,
        Angle,
        Headers,
        Definition,
        Config,
        Resolved,
        Streams,
        BuildSldprt(Streams, FormatVersion=4),
        Cut,
        InputValue,
    )
