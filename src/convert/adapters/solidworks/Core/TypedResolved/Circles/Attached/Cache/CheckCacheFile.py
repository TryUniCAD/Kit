from pathlib import PureWindowsPath
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the file identity is a stored self reference and never needs to be loaded to resolve the local body
def CheckCacheFile(
    LinkValue: NativeLink, FileValue: ArchiveNode, Configuration: str
) -> None:
    RootFields = LinkValue.ConfigValue.RootValue.FieldsValue
    ModelName = RequireNative(RootFields.get("f18"), "moNodeName_c").FieldsValue.get(
        "f08"
    )
    Fields = FileValue.FieldsValue
    Shared = NativeRecord(Fields.get("shared"))
    PartText = RequireNative(Shared.get("h10"), "moCStringHandle_c").FieldsValue.get(
        "f08"
    )
    PathValue = RequireNative(Shared.get("h18"), "moCStringHandle_c").FieldsValue.get(
        "f08"
    )
    Config = NativeRecord(Fields.get("refcfg"))
    if (
        type(ModelName) is not str
        or type(PathValue) is not str
        or PartText != ModelName
        or PureWindowsPath(PathValue).name.casefold()
        != (ModelName + KPartSuffix).casefold()
        or Shared.get("f28") != LinkValue.ConfigValue.HeaderValue.FieldsValue.get("f70")
        or (Config.get("f08"), Config.get("f10")) != (Configuration, 0)
    ):
        raise ValueError(
            "SOLIDWORKS attached circle chooser file does not identify its own part"
        )
