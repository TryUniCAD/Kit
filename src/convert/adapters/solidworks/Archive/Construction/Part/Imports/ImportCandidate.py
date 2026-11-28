from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# import consumers need the actual linked construction graph and the bytes produced from it
@DataClass(frozen=True, slots=True)
class ImportCandidate:
    SystemValue: PartSystem
    FeatureValue: ArchiveNode
    AtomId: int
    HeadersValue: tuple[ArchiveNode, ArchiveNode, ArchiveNode]
    DefinitionValue: ModelDefGraph
    ConfigValue: ConfigGraph
    ResolvedValue: ResolvedGraph
    StreamsValue: Mapping[str, bytes]
    BytesValue: bytes
