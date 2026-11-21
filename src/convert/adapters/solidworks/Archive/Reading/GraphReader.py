from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader


# archive bodies share a cursor and map while each native stream supplies its grammar
@DataClass(slots=True)
class GraphReader:
    Cursor: BinaryReader
    MapValue: ArchiveMaps
    BodyReader: Callable[[GraphReader, ArchiveNode], None]
    NestingDepth: int = 0
    NodeFactory: Callable[[RuntimeClass | ExternalClass], ArchiveNode] | None = None
    RequireCanonicalTags: bool = False
