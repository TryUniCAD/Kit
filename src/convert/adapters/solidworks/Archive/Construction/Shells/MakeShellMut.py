from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    CheckChmfAtom,
    MakeChmfNode,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfGraph import (
    BindChmfAtomMut,
    LogChmfMut,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Shells.MakeShellDim import (
    MakeShellDim,
)
from convert.adapters.solidworks.Archive.Construction.Shells.MakeShellRefs import (
    MakeShellRefs,
)
from convert.adapters.solidworks.Archive.Construction.Shells.OpenShellPlan import (
    OpenShellPlan,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# shell construction starts with the shared empty body feature state and its ordinary inward mode
def InitShellNode(
    Model: ArchiveNode, NameValue: str, Settings: PartBuildInput
) -> ArchiveNode:
    Feature = MakeChmfNode("moShell_c", {})
    InitFeatureMut(Feature, NameValue, Model, Settings.TargetValue)
    Fields = Feature.FieldsValue
    Fields.update(dict.fromkeys(KAtomWords, 0))
    Fields.update({KeyValue: [] for KeyValue in KAtomLists})
    Fields.update(
        f35c=0,
        f368=MakeObList(),
        f388=MakeObList(),
        f4a0=1,
        f6e0=None,
        f758=None,
        f780=MakeObList(),
        f7a0=0,
        f820=0,
        f830=MakeChmfNode("suObList", MakeObList()),
        f838=MakeChmfNode("suObList", MakeObList()),
        f850=None,
    )
    return Feature


# the shell consumes the same stock atom and adds its own selected face and editable thickness
def MakeShellMut(
    Stock: PartCandidate, PlanValue: OpenShellPlan, Settings: PartBuildInput
) -> tuple[ArchiveNode, DimensionGraph]:
    Model = Stock.SystemValue.RootValue
    NextValue = FieldInt(Stock.HeaderValue.FieldsValue, "f08")
    if (
        NextValue != FieldInt(Stock.TopHeader.FieldsValue, "f08")
        or Stock.ResolvedValue.RootsValue[-1] is not Stock.BossValue.FeatureValue
        or Stock.PlanValue != PlanValue.StockValue
    ):
        raise ValueError("shell construction needs the actual pristine stock frontier")
    Allocator = PersistentIds(NextValue)
    Feature = InitShellNode(Model, PlanValue.FeatureName, Settings)
    Driver = MakeShellDim(Model, Feature, PlanValue)
    _ = Allocator.AllocateMut(Driver.DimensionValue, "f50")
    _ = Allocator.AllocateMut(Feature)
    AtomValue = BindChmfAtomMut(Stock, Feature)
    LogChmfMut(Stock, Feature, Settings, Allocator)
    CheckChmfAtom(Stock, Feature, AtomValue)
    CapValue, EdgeValue = MakeShellRefs(Stock, AtomValue)
    Feature.FieldsValue.update(
        f818=Driver.DisplayValue,
        f828=MakeChmfNode("suObList", {"n": 1, "items": [{"o": CapValue}]}),
        f848=EdgeValue,
    )
    Stock.SystemValue.ManagerValue.FieldsValue["f658"] = 1
    return Feature, Driver
