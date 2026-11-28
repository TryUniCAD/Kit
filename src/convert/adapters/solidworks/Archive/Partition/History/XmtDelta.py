from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# retained body history needs each wire inventory and its separate staging bound
@DataClass(frozen=True, slots=True)
class XmtDelta:
    RestoredValue: tuple[XmtNode, ...]
    RemovedValue: tuple[tuple[int, int], ...]
    PreviousValue: tuple[XmtNode, ...]
    CopyCapacity: int
    Qualifiers: Mapping[int, bool]
