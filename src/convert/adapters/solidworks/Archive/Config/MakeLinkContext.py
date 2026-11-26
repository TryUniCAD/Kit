from collections.abc import Mapping
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Cmgr.CmgrGraph import CmgrGraph
from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph


# resolved body mapping depends on the separate manager context without inheriting its object map
def MakeLinkContext(
    ConfigValue: ConfigGraph, ManagerValue: CmgrGraph
) -> Mapping[str, int]:
    if (
        ConfigValue.VersionValue != 19000
        or ManagerValue.VersionValue != ConfigValue.VersionValue
    ):
        raise ValueError(
            "linked SOLIDWORKS graph versions do not match the ordinary current profile"
        )
    WordValue = ManagerValue.RootValue.FieldsValue["f658"]
    if type(WordValue) is not int:
        raise ValueError("SOLIDWORKS manager body mapping context is not an integer")
    return MappingProxyType(
        {
            "model_compressed_stream": 1,
            "model_is_part": int(
                ConfigValue.RootValue.ClassValue.NameValue == "moPart_c"
            ),
            "cmgr_f658": WordValue,
        }
    )
