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
from convert.adapters.solidworks.Archive.Construction.Shells.InitShellNode import (
    InitShellNode,
)


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
