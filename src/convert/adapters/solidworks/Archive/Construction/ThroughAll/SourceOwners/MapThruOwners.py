from convert.adapters.solidworks.Archive.Construction.BodyScope.StockBodyGraph import (
    StockBodyGraph,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Extrusion.ExtrusionGraph import (
    ExtrusionGraph,
)
from convert.adapters.solidworks.Archive.Construction.Profile.ProfileGraph import (
    ProfileGraph,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceInputs.ThruOwnerInput import (
    ThruOwnerInput,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.MapThruAxes import (
    MapThruAxes,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.MapThruBases import (
    MapThruBases,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.MapThruLines import (
    MapThruLines,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.SourceOwners.OwnerBind import (
    OwnerBind,
)


# each generated correspondence must retain a unique actual source identity while leaving unrepresented source owners explicitly outside the component
def MapThruOwners(
    InputValue: ThruOwnerInput,
    SystemValue: PartSystem,
    ProfileValue: ProfileGraph,
    StockValue: ExtrusionGraph,
    CutValue: CutGraph,
    ScopeValue: StockBodyGraph,
) -> tuple[OwnerBind, ...]:
    Result = (
        *MapThruBases(
            InputValue, SystemValue, ProfileValue, StockValue, CutValue, ScopeValue
        ),
        *MapThruLines(InputValue, ProfileValue),
        *MapThruAxes(InputValue, SystemValue, ProfileValue, StockValue, CutValue),
    )
    if len({Value.SourceId for Value in Result}) != len(Result) or any(
        type(Value.SourceId) is not str or not Value.SourceId for Value in Result
    ):
        raise ValueError(
            "source owner correspondence has duplicate or empty identities"
        )
    return Result
