from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# both physical headers must agree with the historical self before an empty path can be local
def CheckWarmSelf(
    LinkValue: NativeLink, FileValue: ArchiveNode, TopHeader: ArchiveNode
) -> None:
    HeaderValue = LinkValue.ConfigValue.HeaderValue
    ConfigSelf, TopSelf = (
        RequireNative(Header.FieldsValue.get("f38"), "moExtObject_c")
        for Header in (HeaderValue, TopHeader)
    )
    RefValue = ConfigSelf.FieldsValue.get("file")
    Shared = NativeRecord(FileValue.FieldsValue.get("shared"))
    if (
        FileValue in (ConfigSelf, TopSelf)
        or not isinstance(RefValue, NativeFileRef)
        or RefValue != TopSelf.FieldsValue.get("file")
        or not RefValue.NameValue
        or RefValue.KindValue != 2
        or RefValue.ConfigValue != "Default"
        or NativeRecord(FileValue.FieldsValue.get("refcfg"))
        != {"f08": RefValue.ConfigValue, "f10": 0}
        or Shared.get("f20") != RefValue.KindValue
        or type(Shared.get("f28")) is not int
        or Shared.get("f28")
        != NativeRecord(ConfigSelf.FieldsValue.get("shared")).get("f28")
        or Shared.get("f28")
        != NativeRecord(TopSelf.FieldsValue.get("shared")).get("f28")
        or RequireNative(Shared.get("h10"), "moCStringHandle_c").FieldsValue.get("f08")
        != RefValue.NameValue
        or RequireNative(Shared.get("h18"), "moCStringHandle_c").FieldsValue.get("f08")
        != RefValue.PathValue
    ):
        raise ValueError(
            "saved chamfer historical file differs from its actual local headers"
        )
