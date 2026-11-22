from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# flat and recursive assembly emitters need one linked graph stage before independently rooted metadata and manager streams are serialized
@DataClass(frozen=True, slots=True)
class AsmGraphState:
    ConfigBytes: bytes
    ConfigValue: ConfigGraph
    ResolvedBytes: bytes
    ResolvedValue: ResolvedGraph
    MatesBytes: bytes
    MatesValue: MatesGraph
    ManagerHeader: ArchiveNode
    DefinitionValue: ModelDefGraph
