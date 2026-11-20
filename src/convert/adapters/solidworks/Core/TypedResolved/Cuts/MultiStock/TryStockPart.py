from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.BindStockModel import (
    BindStockModel,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockCache import (
    ReadStockCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheGeom import (
    StockCacheGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.IsStockConfig import (
    IsStockConfig,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.IsStockModel import (
    IsStockModel,
)


# positive saved reads require both active physical geometry and the actual selected configuration
def TryStockPart(
    Archive: SldprtArchive, Model: NativeModel, Settings: ReadOptions
) -> tuple[NativeModel, StockCacheGeom | None]:
    if not IsStockModel(Model, Settings):
        return Model, None
    try:
        CacheValue = ReadStockCache(Archive)
        if not IsStockConfig(Archive, CacheValue.LinkValue.ConfigValue.VersionValue):
            return Model, None
        Bound = BindStockModel(Model, CacheValue.LinkValue, CacheValue.LineageValue)
    except (ValueError, TypeError, KeyError):
        return Model, None
    return Bound, CacheValue
