from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.BindStockModel import (
    BindStockModel,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.BuildColdGeom import (
    BuildColdGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockPart import (
    ColdStockPart,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdOwners import (
    ReadColdOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.IsStockConfig import (
    IsStockConfig,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.IsStockModel import (
    IsStockModel,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# the cache free path must qualify the same linked history before replacing strict cache failure
def TryColdStock(
    Archive: SldprtArchive, Model: NativeModel, Settings: ReadOptions
) -> tuple[NativeModel, ColdStockPart | None]:
    if not IsStockModel(Model, Settings) or not IsCacheAbsent(Archive):
        return Model, None
    try:
        LinkValue = ReadNativeLink(Archive, Model.active_configuration_id)
        if not IsStockConfig(Archive, LinkValue.ConfigValue.VersionValue):
            return Model, None
        OwnersValue = ReadColdOwners(LinkValue)
        Bound = BindStockModel(Model, LinkValue, OwnersValue)
        return Bound, BuildColdGeom(OwnersValue)
    except (ValueError, TypeError, KeyError, OverflowError):
        return Model, None
