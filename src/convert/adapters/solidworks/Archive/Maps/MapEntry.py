from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# shared map slots must retain their class or object owner explicitly
@DataClass(frozen=True, slots=True)
class MapEntry:
    IndexValue: int
    EntryValue: RuntimeClass | ExternalClass | ArchiveNode

    # invalid slot ownership must fail before a snapshot can seed another stream
    def __post_init__(self) -> None:
        if type(self.IndexValue) is not int:
            raise TypeError("archive map index must be an integer")
        if not 1 <= self.IndexValue <= 0x7FFFFFFF:
            raise ValueError("archive map index exceeds the tag domain")
        if type(self.EntryValue) is RuntimeClass:
            return
        if type(self.EntryValue) is ExternalClass:
            if self.EntryValue.IndexValue != self.IndexValue:
                raise ValueError("external class binding differs from its map slot")
            return
        _ = ArchiveNode.RequireNode(self.EntryValue)
