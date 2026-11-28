from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# source identities need explicit actual generated node or inline record correspondence without reusing native source numbers
@DataClass(frozen=True, slots=True)
class OwnerBind:
    SourceId: str
    RoleValue: str
    OwnerValue: ArchiveNode
    Value: ArchiveNode | Mapping[str, object]
