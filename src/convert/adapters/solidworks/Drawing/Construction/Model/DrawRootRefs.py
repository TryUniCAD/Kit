from collections.abc import MutableMapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# drawing dependencies must preserve actual generated owners without the part only visual and analysis unit objects
@DataClass(frozen=True, slots=True)
class DrawRootRefs:
    DetailFields: MutableMapping[str, object]
    DocumentUnits: ArchiveNode
    ViewValues: tuple[ArchiveNode, ...]
