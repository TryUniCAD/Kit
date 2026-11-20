from dataclasses import dataclass as MakeDataClass

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheBody import (
    StockCacheBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import (
    StockCutLineage,
)
from interchange.brep.Topology.BrepModel import BrepModel


# the saved cache groups physical geometry without claiming whole document projection
@MakeDataClass(frozen=True, slots=True)
class StockCacheGeom:
    BrepValue: BrepModel
    LineageValue: StockCutLineage
    BodyValues: tuple[StockCacheBody, StockCacheBody]
    StreamName: str
