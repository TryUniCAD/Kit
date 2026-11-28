from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# an installation binds semantic value slots to the actual owner needing the attribute
@DataClass(frozen=True, slots=True)
class CylAttrIn:
    OwnerValue: XmtNode
    NameValue: str
    ValuesValue: tuple[tuple[int, ...] | None, ...]
