from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# complete generated assembly results expose their original linked graph and child rather than reconstructing ownership from emitted bytes
@DataClass(frozen=True, slots=True)
class AsmCandidate:
    StateValue: AssemblyState
    ChildValue: PartCandidate
    OccurrenceValues: tuple[ArchiveNode, ...]
    MateValue: ArchiveNode
    HeaderValue: ArchiveNode
    TopHeader: ArchiveNode
    ManagerHeader: ArchiveNode
    DefinitionValue: ModelDefGraph
    ConfigValue: ConfigGraph
    ResolvedValue: ResolvedGraph
    MatesValue: MatesGraph
    StreamsValue: Mapping[str, bytes]
    BytesValue: bytes
