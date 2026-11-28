from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.MakeEndSpec import (
    MakeEndSpec,
)
from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import (
    BindStockMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.BindExtrusionMut import (
    BindExtrudeMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionDimMut import (
    MakeEndDimMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionNodeMut import (
    MakeExtrudeMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThruProfile import (
    MakeThruProfile,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockBossGraph import (
    StockBossGraph,
)


# the second independent prism must retain a live driver without inheriting the cut operation
def MakeStockBoss(
    SystemValue: PartSystem,
    SettingsValue: PartBuildInput,
    PlanValue: ThroughStock,
    Allocator: PersistentIds,
    ManagerValue: dict[str, object],
    IndependentStock: bool,
) -> StockBossGraph:
    TargetValue = SettingsValue.TargetValue
    ProfileValue = MakeThruProfile(SystemValue, SettingsValue, PlanValue, Allocator)
    FeatureValue = MakeExtrudeMut(
        "moICE_c" if IndependentStock else "moExtrusion_c",
        PlanValue.FeatureName,
        SystemValue.RootValue,
        TargetValue,
        Allocator,
    )
    EndInput = BossEndInput(
        PlanValue.DepthValue, False, TargetValue.FileVersion, "blind"
    )
    DriverValue = MakeEndDimMut(
        FeatureValue,
        EndInput,
        1,
        SettingsValue.DesignIntent,
        SettingsValue.SelectedLeader,
        Allocator,
    )
    EndValue = MakeEndSpec(
        "blind",
        False,
        DriverValue.DisplayValue,
        None,
        None,
        None,
        ArchiveNode(RuntimeClass("moFromEndSpec_c", 1), {"t": 0}),
    )
    BindExtrudeMut(
        FeatureValue, ProfileValue, EndValue, IndependentStock=IndependentStock
    )
    AtomValue = BindStockMut(ManagerValue, FeatureValue, AppendMember=IndependentStock)
    return StockBossGraph(FeatureValue, ProfileValue, DriverValue, AtomValue)
