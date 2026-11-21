from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheBody import StockCacheBody
from interchange.brep.Topology.BrepModel import BrepModel


# a saved revolve cache carries the actual bodies after its parametric lineage is proved
@Dataclass(frozen=True, slots=True)
class RevCutCache:
    BrepValue: BrepModel
    BodyValues: tuple[StockCacheBody, StockCacheBody]
    StreamName: str
