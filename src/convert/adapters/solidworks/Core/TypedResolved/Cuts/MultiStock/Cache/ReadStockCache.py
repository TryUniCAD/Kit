from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.MapStockBrep import (
    MapStockBrep,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadCacheBodies import (
    ReadCacheBodies,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockData import (
    ReadStockData,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheGeom import (
    StockCacheGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadTwoStockCut import (
    ReadTwoStockCut,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# an active partition can preserve physical grouping after the actual selected cut lineage qualifies
def ReadStockCache(Archive: SldprtArchive, ConfigId: int = 0) -> StockCacheGeom:
    LinkValue = ReadNativeLink(Archive, ConfigId)
    Lineage = ReadTwoStockCut(LinkValue)
    StreamName = LinkValue.ConfigName + "-Partition"
    NodesValue, ModelValue = ReadStockData(Archive, StreamName)
    BodyValues = ReadCacheBodies(NodesValue, Lineage)
    BrepValue = MapStockBrep(NodesValue, ModelValue, BodyValues)
    return StockCacheGeom(BrepValue, Lineage, BodyValues, StreamName)
