from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadWorldBodies import (
    ReadWorldBodies,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheBody import (
    StockCacheBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import (
    StockCutLineage,
)


# the world must own exactly the two surviving atoms without depending on body order
def ReadCacheBodies(
    NodesValue: Mapping[int, XmtNode], Lineage: StockCutLineage
) -> tuple[StockCacheBody, StockCacheBody]:
    AtomsValue = Lineage.AtomsValue
    Untouched = Lineage.StockValues[1 - AtomsValue.SelectedIndex].NodeValue
    Producer = Lineage.CutValue.NodeValue
    return ReadWorldBodies(NodesValue, AtomsValue, Untouched, Producer)
