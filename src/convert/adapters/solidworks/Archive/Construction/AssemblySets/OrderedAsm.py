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


# ordered assembly results retain every actual mate alongside the shared generated child parent graph and independently serialized stream contexts
@DataClass(frozen=True, slots=True)
class OrderedAsm:
    StateValue: AssemblyState
    ChildValue: PartCandidate
    OccurrenceValues: tuple[ArchiveNode, ...]
    MateValues: tuple[ArchiveNode, ...]
    HeaderValue: ArchiveNode
    TopHeader: ArchiveNode
    ManagerHeader: ArchiveNode
    DefinitionValue: ModelDefGraph
    ConfigValue: ConfigGraph
    ResolvedValue: ResolvedGraph
    MatesValue: MatesGraph
    StreamsValue: Mapping[str, bytes]
    BytesValue: bytes
