from collections.abc import Callable
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag


# graph storage computes map order while explicit callbacks own body serialization
@DataClass(frozen=True, slots=True)
class ObjectStore:
    MapValue: ArchiveMaps
    TagWriter: Callable[[ArchiveTag], None]
    ClassWriter: Callable[[RuntimeClass], None]
    BodyWriter: Callable[[ArchiveNode], None]
