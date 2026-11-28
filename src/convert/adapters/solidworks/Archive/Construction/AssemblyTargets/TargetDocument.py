from collections.abc import Mapping
from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph


# recursive assembly placement needs one shared contract retaining actual generated definition owners without decoding or reconstructing the child
@DataClass(frozen=True, slots=True)
class TargetDocument:
    RootValue: ArchiveNode
    ManagerValue: ArchiveNode
    CurrentConfig: ArchiveNode
    HeaderValue: ArchiveNode
    TopHeader: ArchiveNode
    ManagerHeader: ArchiveNode
    FeatureValues: tuple[ArchiveNode, ...]
    BoundsValue: Mapping[str, float]
    ReferenceValues: tuple[ArchiveNode, ...]
    ChildTargets: tuple["TargetDocument", ...]
    ActivityValue: int
    ConfigValue: ConfigGraph
    ResolvedValue: ResolvedGraph
    StreamsValue: Mapping[str, bytes]
    BytesValue: bytes
