from collections.abc import Mapping
from dataclasses import dataclass as DataClass, field as DataField

from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# stream modes and concrete dispatch belong to the owning archive rather than individual nodes
@DataClass(slots=True)
class BodyContext:
    VersionValue: int
    LayoutsValue: Mapping[str, tuple[NativeField, ...]]
    VirtualValue: Mapping[tuple[str, int], str | int | bool | None]
    SchemasValue: Mapping[str, tuple[int, ...]]
    UsageValue: BodyUsage = DataField(default_factory=BodyUsage)
    FlagsValue: dict[str, int] = DataField(default_factory=dict[str, int])
    DirectNodes: tuple[ArchiveNode, ...] = ()
    PendingNodes: list[ArchiveNode] = DataField(default_factory=list[ArchiveNode])
