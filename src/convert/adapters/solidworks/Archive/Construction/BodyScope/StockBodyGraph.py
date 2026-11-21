from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.ThroughAll.ThroughStock import (
    ThroughStock,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# selected body consumers need the actual stock model and archive owners without reconstructing them from integer identities
@DataClass(frozen=True, slots=True)
class StockBodyGraph:
    StockValue: ThroughStock
    RootValue: ArchiveNode
    FeatureValue: ArchiveNode
    AtomValue: ArchiveNode
    WrapperValue: ArchiveNode
    CutValue: ArchiveNode
