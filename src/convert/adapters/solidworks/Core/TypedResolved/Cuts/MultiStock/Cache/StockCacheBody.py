from dataclasses import dataclass as MakeDataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# retained body identities allow a later timeline to link both physical solid results
@MakeDataClass(frozen=True, slots=True)
class StockCacheBody:
    AtomValue: ArchiveNode
    ProducerValue: ArchiveNode
    KernelValue: XmtNode
    AtomId: int
    NameValue: str

    # a portable identity must follow the actual surviving atom across save order changes
    @property
    def DesignId(self) -> str:
        return f"sldprt:body:atom:{self.AtomId}"
