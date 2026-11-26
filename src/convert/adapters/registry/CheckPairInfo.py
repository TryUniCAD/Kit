from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.WritePolicy import GetFormatKey
from convert.adapters.registry.RegistryErrors import RegistryError


# a narrow writer may advertise fewer input semantics and aliases while retaining the established format identity
def CheckPairInfo(ReaderInfo: AdapterInfo, WriterInfo: AdapterInfo) -> None:
    if (
        ReaderInfo.FormatId != WriterInfo.FormatId
        or ReaderInfo.DisplayName != WriterInfo.DisplayName
        or ReaderInfo.VersionText != WriterInfo.VersionText
        or not WriterInfo.Capabilities <= ReaderInfo.Capabilities
    ):
        raise RegistryError(
            f"reader and writer metadata differ for {ReaderInfo.FormatId}"
        )
    for WriterNames, ReaderNames in (
        (WriterInfo.Extensions, ReaderInfo.Extensions),
        (WriterInfo.AliasNames, ReaderInfo.AliasNames),
        (WriterInfo.MediaTypes, ReaderInfo.MediaTypes),
        (WriterInfo.PartExts, ReaderInfo.PartExts),
        (WriterInfo.AssemblyExts, ReaderInfo.AssemblyExts),
    ):
        if not set(map(GetFormatKey, WriterNames)) <= set(
            map(GetFormatKey, ReaderNames)
        ):
            raise RegistryError(
                f"writer declares destinations outside {ReaderInfo.FormatId}"
            )
