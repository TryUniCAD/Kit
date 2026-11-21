from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.BodyScope.StockBodyGraph import (
    StockBodyGraph,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.ExtrusionGraph import (
    ExtrusionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.OwnerBind import (
    OwnerBind,
)


# generated owners are an explicit component result without a complete container or implied source conversion status
@DataClass(frozen=True, slots=True)
class ThruOwnerGraph:
    SystemValue: PartSystem
    StockProfile: ProfileGraph
    StockValue: ExtrusionGraph
    CutValue: CutGraph
    ScopeValue: StockBodyGraph
    BindValues: tuple[OwnerBind, ...]
    IdsValue: PersistentIds
