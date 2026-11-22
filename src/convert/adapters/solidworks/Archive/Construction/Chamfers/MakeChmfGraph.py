from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import (
    BindStockMut,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfEdgeRoles import (
    PickChmfRoles,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfPlan import ChmfPlan
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    MakeChmfNode,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfStockGeom import (
    MakeChmfStock,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfDrivers import (
    MakeChmfDrivers,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.MakeChmfRefs import (
    MakeChmfRefs,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import (
    DimensionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import (
    MakeRootLog,
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
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.CheckChmfMode import (
    CheckChmfMode,
)


# shape and mode fields encode the ordinary cold single edge feature
def InitChmfNode(
    Model: ArchiveNode,
    PlanValue: ChmfPlan,
    Settings: PartBuildInput,
) -> ArchiveNode:
    Feature = MakeChmfNode("Chamfer_c", {})
    InitFeatureMut(Feature, PlanValue.FeatureName, Model, Settings.TargetValue)
    if PlanValue.AngleValue is not None and PlanValue.OtherSetback is not None:
        raise ValueError("the chamfer cannot own an angle and a second setback")
    ModeWord = 18
    if PlanValue.AngleValue is not None:
        ModeWord = 1
    elif PlanValue.OtherSetback is not None:
        ModeWord = 2
    Fields = Feature.FieldsValue
    Fields.update(dict.fromkeys(KAtomWords, 0))
    Fields.update({NameValue: [] for NameValue in KAtomLists})
    Fields.update(
        f35c=0,
        f368={"n": 0, "items": []},
        f388={"n": 0, "items": []},
        f4a0=1,
        f6e0=None,
        f758=None,
        f780={"n": 0, "items": []},
        f7a0=0,
        f860=0,
        f8a0=10,
        f878=0,
        f8c0=ModeWord,
        f87c=0,
        has_f808=0,
        f8f0=1,
        f8c8={"n": 0, "items": []},
    )
    Fields.update(
        dict.fromkeys(
            (
                "f818",
                "f820",
                "f8b0",
                "f8b8",
                "f828",
                "f830",
                "f838",
                "f840",
                "f848",
                "f850",
                "f858",
            ),
            None,
        )
    )
    return Feature


# the converted stock atom remains the same object with the chamfer as its latest modifier
def BindChmfAtomMut(Stock: PartCandidate, Feature: ArchiveNode) -> ArchiveNode:
    Manager = Stock.SystemValue.RootValue.FieldsValue["fd88"]
    if not isinstance(Manager, dict) or Manager["atoms"]:
        raise ValueError(
            "chamfer needs the fresh stock part's actual unused atom manager"
        )
    AtomValue = BindStockMut(
        CastValue(dict[str, object], Manager), Stock.BossValue.FeatureValue
    )
    AtomValue.FieldsValue["f130"] = Feature.FieldsValue["f08"]
    Feature.FieldsValue["f538"] = AtomValue
    return AtomValue


# fresh creation events extend both headers using the actual producer and chamfer nodes
def LogChmfMut(
    Stock: PartCandidate,
    Feature: ArchiveNode,
    Settings: PartBuildInput,
    Allocator: PersistentIds,
) -> None:
    BossNode = Stock.BossValue.FeatureValue
    SetCfgStampMut(Stock.CurrentConfig, Allocator)
    for Header in (Stock.HeaderValue, Stock.TopHeader):
        LogFields = ArchiveNode.RequireNode(Header.FieldsValue["f20"]).FieldsValue
        Items = LogFields["items"]
        if not isinstance(Items, tuple):
            raise ValueError(
                "the cold chamfer requires ordered creation logs in both headers"
            )
        LogFields["items"] = (
            *Items,
            *(
                MakeRootLog(Owner, Settings.HeaderValue)
                for Owner in (BossNode, Feature)
            ),
        )
        Header.FieldsValue["f08"] = Allocator.NextValue


# the linked feature adds its live dimensions before the shared persistent allocation of the chamfer
def MakeChmfMut(
    Stock: PartCandidate,
    PlanValue: ChmfPlan,
    Settings: PartBuildInput,
) -> tuple[ArchiveNode, tuple[DimensionGraph, ...]]:
    Model = Stock.SystemValue.RootValue
    StockId = FieldInt(Stock.HeaderValue.FieldsValue, "f08")
    if (
        StockId != FieldInt(Stock.TopHeader.FieldsValue, "f08")
        or Stock.ResolvedValue.RootsValue[-1] is not Stock.BossValue.FeatureValue
    ):
        raise ValueError(
            "chamfer must extend the same actual stock and header allocator frontier"
        )
    Roles = PickChmfRoles(MakeChmfStock(Stock), PlanValue.EdgeValue)
    Allocator = PersistentIds(StockId)
    Feature = InitChmfNode(Model, PlanValue, Settings)
    Drivers = MakeChmfDrivers(Model, Feature, PlanValue)
    for SlotName, Driver in Drivers:
        _ = Allocator.AllocateMut(Driver.DimensionValue, "f50")
        Feature.FieldsValue[SlotName] = Driver.DisplayValue
    _ = Allocator.AllocateMut(Feature)
    AtomValue = BindChmfAtomMut(Stock, Feature)
    LogChmfMut(Stock, Feature, Settings, Allocator)
    Feature.FieldsValue.update(MakeChmfRefs(Stock, Feature, AtomValue, Roles))
    CheckChmfMode(Feature, FieldInt(Feature.FieldsValue, "f8c0"))
    Stock.SystemValue.ManagerValue.FieldsValue["f658"] = 1
    return Feature, tuple(Driver for _, Driver in Drivers)
