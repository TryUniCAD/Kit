from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrInfo import ReadCmgrInfo
from convert.adapters.solidworks.Container.Container import SldprtArchive


# stock projection requires the same actual active configuration in both manager slots
def IsStockConfig(Archive: SldprtArchive, VersionValue: int) -> bool:
    Manager = ReadCmgrInfo(Archive.require("Contents/CMgr"), VersionValue)
    return Manager.get("configurations") == (
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
    )
