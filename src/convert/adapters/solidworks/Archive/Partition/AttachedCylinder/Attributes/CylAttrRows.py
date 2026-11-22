from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the active world and rollback journal share the actual allocated attribute graph through explicit links
@DataClass(frozen=True, slots=True)
class CylAttrRows:
    NodesValue: tuple[XmtNode, ...]
    OwnerHeads: dict[int, int]
    TypeHeads: dict[str, int]
    HiddenAllocations: int
