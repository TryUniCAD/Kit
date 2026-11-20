from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheGeom import (
    StockCacheGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockPart import (
    ColdStockPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.TryColdStock import (
    TryColdStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.TryStockPart import (
    TryStockPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadNoCache import (
    ReadNoCache,
)


# exact saved and cold stock paths must qualify before ordinary geometry can substitute for cache data
def ReadPartShape(
    Archive: SldprtArchive, Model: NativeModel, Settings: ReadOptions, BodyId: str
) -> tuple[
    NativeModel, StockCacheGeom | None, ColdStockPart | None, PartGeometry | None
]:
    Model, SavedValue = TryStockPart(Archive, Model, Settings)
    if SavedValue is not None or not Settings.include_brep:
        return Model, SavedValue, None, None
    Model, ColdValue = TryColdStock(Archive, Model, Settings)
    if ColdValue is not None:
        return Model, None, ColdValue, ColdValue.GeometryValue
    return Model, None, None, ReadNoCache(Archive, Model, BodyId)
