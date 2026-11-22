from convert.adapters.solidworks.Archive.Construction.Files.ReadFileText import (
    ReadFileText,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# native saves may identify local files without populating their absolute path field
def LocalFileKey(FileValue: ArchiveNode) -> tuple[object, ...]:
    Fields = FileValue.FieldsValue
    Shared = NativeRecord(Fields.get("shared"))
    Config = NativeRecord(Fields.get("refcfg"))
    ConfigName = Config.get("f08")
    if isinstance(ConfigName, CStringValue):
        ConfigName = ConfigName.TextValue
    PathFields = RequireNative(Shared.get("h18"), "moCStringHandle_c").FieldsValue
    PathText = PathFields.get("text", PathFields.get("f08"))
    if PathText == "":
        WireValue = PathFields.get("value")
        if WireValue is not None and (
            not isinstance(WireValue, CStringValue) or WireValue.TextValue != ""
        ):
            raise ValueError("SOLIDWORKS shell local path representations differ")
    else:
        PathText = ReadFileText(Shared.get("h18"))
    return (
        ReadFileText(Shared.get("h10")),
        PathText,
        Shared.get("f28"),
        Shared.get("f08"),
        Shared.get("f20"),
        ConfigName,
        Config.get("f10"),
    )


# all carried references must point at the same real local part and configuration
def CheckShellFile(
    FileValue: ArchiveNode, PartHeader: ArchiveNode, TopHeader: ArchiveNode
) -> None:
    ConfigSelf, TopSelf = (
        RequireNative(Header.FieldsValue.get("f38"), "moExtObject_c")
        for Header in (PartHeader, TopHeader)
    )
    FileKey = LocalFileKey(FileValue)
    if (
        FileValue in (ConfigSelf, TopSelf)
        or FileKey[-2:] != ("Default", 0)
        or any(FileKey != LocalFileKey(Value) for Value in (ConfigSelf, TopSelf))
    ):
        raise ValueError(
            "SOLIDWORKS shell reference targets another file or configuration"
        )
