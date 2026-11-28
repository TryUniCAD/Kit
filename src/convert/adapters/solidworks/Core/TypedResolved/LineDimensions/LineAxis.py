from collections.abc import Mapping
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# embedded unary relations retain their actual owner row and concrete local line handle
@Dataclass(frozen=True, slots=True)
class LineAxis:
    IndexValue: int
    LineValue: int
    CodeValue: int
    HandleValue: ArchiveNode
    OwnerValue: Mapping[str, object]
