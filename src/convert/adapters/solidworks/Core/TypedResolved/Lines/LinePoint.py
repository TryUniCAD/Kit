from collections.abc import Mapping
from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# embedded vertices need identities distinct from line markers and tagged adjacency handles
@Dataclass(frozen=True, slots=True)
class LinePoint:
    IndexValue: int
    CreationId: int
    PositionValue: tuple[float, float]
    HandlesValue: tuple[ArchiveNode, ...]
    FieldsValue: Mapping[str, object]
