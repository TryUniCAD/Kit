from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# linked assembly serialization must expose actual map contexts and metadata owners alongside computed streams for independent process verification
@DataClass(frozen=True, slots=True)
class AssemblyStreams:
    StreamsValue: dict[str, bytes]
    ConfigValue: ConfigGraph
    ResolvedValue: ResolvedGraph
    MatesValue: MatesGraph
    ManagerHeader: ArchiveNode
    DefinitionValue: ModelDefGraph
