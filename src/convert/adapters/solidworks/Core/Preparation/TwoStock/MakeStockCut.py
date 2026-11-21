from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeBodyRef import (
    MakeBodyRef,
)
from convert.adapters.solidworks.Archive.Construction.Circles.MakeCircleFeat import (
    MakeCircleFeat,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThruCutMut import (
    MakeThruCutMut,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughEndInput import (
    ThroughEndInput,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockBossGraph import (
    StockBossGraph,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.TwoStockPlan import (
    TwoStockPlan,
)


# the cut references the actual earlier stock so native regeneration can assign result bodies
def MakeStockCut(
    SystemValue: PartSystem,
    SettingsValue: PartBuildInput,
    PlanValue: TwoStockPlan,
    FrontGraph: StockBossGraph,
    Allocator: PersistentIds,
) -> CutGraph:
    RootValue = SystemValue.RootValue
    Target = SettingsValue.TargetValue
    AxisValue = PlanValue.StockValues[0].AxisValue
    Profile = MakeCircleFeat(
        PlanValue.CutSketchName,
        RootValue,
        SystemValue.SystemValues.PlaneValues[AxisValue],
        AxisValue,
        PlanValue.CircleValue,
        Target,
        Allocator,
    )
    CutValue = MakeThruCutMut(
        PlanValue.CutName,
        RootValue,
        Profile,
        ThroughEndInput("through_all", True, Target.FileVersion),
        Target,
        Allocator,
    )
    Wrapper = MakeBodyRef(RootValue, FrontGraph.FeatureValue, FrontGraph.AtomValue)
    CutValue.FeatureValue.FieldsValue.update(
        f544=1, has_f548=1, f548={"n": 1, "items": [{"o": Wrapper}]}
    )
    return CutValue
