from collections.abc import Callable
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Tags.ArchiveTag import ArchiveTag


# graph decoding shares identity state while explicit callbacks own all field parsing
@DataClass(frozen=True, slots=True)
class ObjectRead:
    MapValue: ArchiveMaps
    TagReader: Callable[[], ArchiveTag]
    ClassReader: Callable[[], RuntimeClass]
    BodyReader: Callable[[ArchiveNode], None]
    NodeFactory: Callable[[RuntimeClass | ExternalClass], ArchiveNode]
    ReadOffset: Callable[[], int]
