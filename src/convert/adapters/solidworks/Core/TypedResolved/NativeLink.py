from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# semantic readers need the actual linked graph and stream ownership without copying archive nodes
@DataClass(frozen=True, slots=True)
class NativeLink:
    ConfigValue: ConfigGraph
    ResolvedValue: ResolvedGraph
    ConfigName: str
    StreamName: str
    ManagerValue: CmgrGraph | None = None
