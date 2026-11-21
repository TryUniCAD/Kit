from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass as DataClass, field as DataField

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# typed body serialization shares existing identity maps while owning only its output buffer
@DataClass(slots=True)
class BodyWriter:
    MapValue: ArchiveMaps
    ContextValue: BodyContext
    NodeBody: Callable[[BodyWriter, ArchiveNode], None]
    OutputValue: bytearray = DataField(default_factory=bytearray)
    NestingDepth: int = 0
