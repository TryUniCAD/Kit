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
    MakeSelRevRows,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.SelectedCut.ProjectSelectedRevolve import (
    ProjectSelRev,
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
def MakeRevStock(
    System: PartSystem,
    InputValue: PartBuildInput,
    PlanValue: RevolvePlan,
    Allocator: PersistentIds,
    *,
    IsFirst: bool,
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode]:
    Profile, AxisOwner = MakeRevProfMut(System, InputValue, PlanValue, Allocator)
    Feature, _, _, _ = MakeRevFeatMut(
        System, Profile, AxisOwner, InputValue, PlanValue, Allocator
    )
    Feature.FieldsValue.update(f870=int(IsFirst), f544=1)
    Manager = CastValue(dict[str, object], System.RootValue.FieldsValue["fd88"])
    AtomNode = BindStockMut(Manager, Feature, AppendMember=True)
    return Profile.ProfileValue, Feature, AtomNode


# the complete selected stock part allocates two body atoms and the cut from the same neutral ownership graph
def MakeSelRevPart(
    DocumentValue: CadDocument, InputValue: PartBuildInput
) -> RevolvePart:
    PlanValue = ProjectSelRev(DocumentValue)
    First, Second, Cutter = PlanValue.OperationsValue
    ExtraNames = (
        Second.SketchName,
        Second.FeatureName,
        Cutter.SketchName,
        Cutter.FeatureName,
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
    FirstProfile, FirstFeature, FirstAtom = MakeRevStock(
        System, InputValue, First, Allocator, IsFirst=True
    )
    SecondProfile, SecondFeature, SecondAtom = MakeRevStock(
        System, InputValue, Second, Allocator, IsFirst=False
    )
    Profile, AxisOwner = MakeRevProfMut(System, InputValue, Cutter, Allocator)
    Feature, Reference, EndNode, Angle = MakeRevFeatMut(
        System, Profile, AxisOwner, InputValue, Cutter, Allocator, IsCut=True
    )
    Stock, AtomNode = ((FirstFeature, FirstAtom), (SecondFeature, SecondAtom))[
        PlanValue.SelectedIndex
    ]
    Wrapper = MakeBodyRef(System.RootValue, Stock, AtomNode)
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
    KeyRows = MakeSelRevRows(
        System.FeatureValues, Profiles, Features, PlanValue.OperationsValue
    )
    Streams, Config, Resolved = EmitRevStreams(
        System, Roots, Headers, Definition, InputValue, Cutter, KeyRowsValue=KeyRows
    )
    return RevolvePart(
        System,
        Profile,
        Feature,
        Reference,
        EndNode,
        Angle,
        Headers,
        Definition,
        Config,
        Resolved,
        Streams,
        BuildSldprt(Streams, FormatVersion=4),
        Cutter,
        InputValue,
    )
