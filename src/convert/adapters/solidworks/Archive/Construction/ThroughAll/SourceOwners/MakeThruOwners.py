from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import (
    MakeBlindMut,
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
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.CheckThruInput import (
    CheckThruInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.MapThruOwners import (
    MapThruOwners,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.ThruOwnerGraph import (
    ThruOwnerGraph,
)


# safe source geometry owners must use shared factories without emitting a stripped complete document or replaying its native metadata
def MakeThruOwners(
    InputValue: ThruOwnerInput, SettingsValue: PartBuildInput
) -> ThruOwnerGraph:
    CheckThruInput(InputValue, SettingsValue)
    Stock = InputValue.ShapeValue.StockValue
    IdsValue = PersistentIds()
    SystemValue = MakePartBaseMut(SettingsValue, Stock, IdsValue)
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
