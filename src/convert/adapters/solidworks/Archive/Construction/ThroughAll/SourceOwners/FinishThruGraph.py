from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import (
    MakeBlindMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThruProfile import (
    MakeThruProfile,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.MakeThruCutPart import (
    MakeThruCutPart,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.BindScopeMut import (
    BindScopeMut,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.MapThruOwners import (
    MapThruOwners,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.ThruOwnerGraph import (
    ThruOwnerGraph,
)


from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)


# both fresh and explicit source settings must share one profile cut scope and correspondence construction sequence
def FinishThruGraph(
    InputValue: ThruOwnerInput,
    SettingsValue: PartBuildInput,
    SystemValue: PartSystem,
    IdsValue: PersistentIds,
) -> ThruOwnerGraph:
    Stock = InputValue.ShapeValue.StockValue
    Profile = MakeThruProfile(SystemValue, SettingsValue, Stock, IdsValue)
    BossValue = MakeBlindMut(
        Stock.FeatureName,
        SystemValue.RootValue,
        Profile,
        BossEndInput(Stock.DepthValue, False, 19000, "mid_plane"),
        SettingsValue.TargetValue,
        IdsValue,
        SettingsValue.DesignIntent,
        SettingsValue.SelectedLeader,
    )
    CutValue = MakeThruCutPart(
        SystemValue, SettingsValue, InputValue.ShapeValue, IdsValue
    )
    ScopeValue = BindScopeMut(InputValue, SystemValue, BossValue, CutValue)
    BindValues = MapThruOwners(
        InputValue, SystemValue, Profile, BossValue, CutValue, ScopeValue
    )
    return ThruOwnerGraph(
        SystemValue, Profile, BossValue, CutValue, ScopeValue, BindValues, IdsValue
    )
