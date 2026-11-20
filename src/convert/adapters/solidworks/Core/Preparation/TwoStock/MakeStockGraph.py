from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.MakeStockBoss import (
    MakeStockBoss,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.MakeStockCut import (
    MakeStockCut,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.TwoStockGraph import (
    TwoStockGraph,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.TwoStockPlan import (
    TwoStockPlan,
)


# graph construction must allocate both historical bodies before instantiating the selected tool
def MakeStockGraph(
    SettingsValue: PartBuildInput, PlanValue: TwoStockPlan
) -> TwoStockGraph:
    Allocator = PersistentIds()
    FrontPlan, RightPlan = PlanValue.StockValues
    SystemValue = MakePartBaseMut(SettingsValue, FrontPlan, Allocator)
    Manager = SystemValue.RootValue.FieldsValue.get("fd88")
    if (
        not isinstance(Manager, dict)
        or Manager.get("n6c") != 0
        or Manager.get("atoms") not in ([], ())
        or Manager.get("fa8") != 0
    ):
        raise ValueError("two-stock graph requires its fresh root atom manager")
    ManagerValue = CastValue(dict[str, object], Manager)
    FrontGraph = MakeStockBoss(
        SystemValue, SettingsValue, FrontPlan, Allocator, ManagerValue, False
    )
    RightGraph = MakeStockBoss(
        SystemValue, SettingsValue, RightPlan, Allocator, ManagerValue, True
    )
    CutValue = MakeStockCut(
        SystemValue, SettingsValue, PlanValue, FrontGraph, Allocator
    )
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    return TwoStockGraph(SystemValue, (FrontGraph, RightGraph), CutValue, Allocator)
