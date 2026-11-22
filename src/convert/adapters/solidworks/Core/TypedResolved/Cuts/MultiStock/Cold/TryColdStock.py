from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.BindColdModel import (
    BindColdModel,
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
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import (
    CheckPrismMgr,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoot import (
    CheckPrismRoot,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# no active or malformed cached payload may fall through to two stock reconstruction
def TryColdStock(
    Archive: SldprtArchive, Model: NativeModel
) -> tuple[NativeModel, ColdStockPart | None]:
    if (
        Model.active_configuration_id != 0
        or Model.equations
        or tuple(
            (Config.configuration_id, Config.name) for Config in Model.configurations
        )
        != ((0, "Default"),)
        or tuple(Operation.kind for Operation in Model.operations)
        != ("join", "join", "cut")
        or not IsCacheAbsent(Archive)
    ):
        return Model, None
    try:
        LinkValue = ReadNativeLink(Archive, Model.active_configuration_id)
        Manager = ReadCmgrMut(Archive.require("Contents/CMgr"), 19000)
        CheckPrismMgr(Manager)
        Configuration = RequireNative(Manager.RootValue.FieldsValue.get("f360"))
        if ReadNodeName(Configuration) != Model.configurations[0].name:
            return Model, None
        CheckPrismRoot(LinkValue.ConfigValue.RootValue, 2)
        OwnersValue = ReadColdOwners(LinkValue)
        if OwnersValue.SelectedIndex != 0:
            return Model, None
        return BindColdModel(Model, OwnersValue), BuildColdGeom(OwnersValue)
    except (KeyError, TypeError, ValueError, OverflowError):
        return Model, None
