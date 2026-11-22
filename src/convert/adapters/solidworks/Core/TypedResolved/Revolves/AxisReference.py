from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the selected line retains component profile index and permanent identity as distinct ownership domains
@Dataclass(frozen=True, slots=True)
class AxisReference:
    WrapperValue: ArchiveNode
    SelectionValue: ArchiveNode
    HandleValue: ArchiveNode
    IndexValue: int
    MarkValue: int
