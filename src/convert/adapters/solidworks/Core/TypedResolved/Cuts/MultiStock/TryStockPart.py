from dataclasses import replace as ReplaceValue

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrInfo import ReadCmgrInfo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.ReadStockCache import (
    ReadStockCache,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheGeom import (
    StockCacheGeom,
)
from convert.adapters.solidworks.Core.TypedResolved.ProjectTyped import ProjectTyped

# the ordinary compatibility diagnostic identifies a candidate without admitting its history
KLegacyStop = "multiple operation histories are outside typed blind topology"


# positive saved reads require both active physical geometry and the actual selected configuration
def TryStockPart(
    Archive: SldprtArchive, Model: NativeModel, Settings: ReadOptions
) -> tuple[NativeModel, StockCacheGeom | None]:
    if (
        not Settings.include_brep
        or Settings.extract_raw_brep
        or Model.active_configuration_id != 0
        or Model.equations
        or Model.TypedGraph.get("diagnostic") != KLegacyStop
        or tuple((Value.configuration_id, Value.name) for Value in Model.configurations)
        != ((0, "Default"),)
        or tuple(Value.kind for Value in Model.operations) != ("join", "join", "cut")
    ):
        return Model, None
    try:
        CacheValue = ReadStockCache(Archive)
        Manager = ReadCmgrInfo(
            Archive.require("Contents/CMgr"),
            CacheValue.LinkValue.ConfigValue.VersionValue,
        )
        if Manager.get("configurations") != (
            {
                "name": "Default",
                "comment": "",
                "alternate_name": "",
                "feature_description": "",
                "native_object_id": 0,
                "native_class": "moPartConfiguration_c",
                "selected_by_f360": True,
                "selected_by_f368": True,
            },
        ):
            return Model, None
        Bound = ProjectTyped(
            Model, CacheValue.LinkValue, StockValue=CacheValue.LineageValue
        )
    except (ValueError, TypeError, KeyError):
        return Model, None
    return (
        ReplaceValue(
            Bound,
            diagnostics=tuple(
                Message
                for Message in Bound.diagnostics
                if Message != f"typed resolved semantics unavailable: {KLegacyStop}"
            ),
        ),
        CacheValue,
    )
