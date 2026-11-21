from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import (
    MakePartBaseMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.CheckThruInput import (
    CheckThruInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.FinishThruGraph import (
    FinishThruGraph,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.ThruOwnerGraph import (
    ThruOwnerGraph,
)


# safe source geometry owners must use shared factories without emitting a stripped complete document or replaying its native metadata
def MakeThruOwners(
    InputValue: ThruOwnerInput, SettingsValue: PartBuildInput
) -> ThruOwnerGraph:
    CheckThruInput(InputValue, SettingsValue)
    IdsValue = PersistentIds()
    SystemValue = MakePartBaseMut(
        SettingsValue, InputValue.ShapeValue.StockValue, IdsValue
    )
    return FinishThruGraph(InputValue, SettingsValue, SystemValue, IdsValue)
