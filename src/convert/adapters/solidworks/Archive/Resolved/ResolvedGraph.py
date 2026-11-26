from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# resolved roots and inline configuration records must retain the exact inherited object identities
@DataClass(frozen=True, slots=True)
class ResolvedGraph:
    RootsValue: tuple[ArchiveNode | None, ...]
    ExtraFields: MutableMapping[str, object] | None
    MapValue: MapSnapshot
    MapBase: int
    VersionValue: int
    ContextValue: Mapping[str, int]
    ReportValue: Mapping[str, object]
