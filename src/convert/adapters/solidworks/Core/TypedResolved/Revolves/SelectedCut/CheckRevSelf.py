from collections.abc import Iterable

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Header.NativeFileRef import NativeFileRef
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevFaceRef import RevFaceRef


# representations must share the actual local part identity without authorizing an external lookup
def CheckRevSelf(Header: ArchiveNode, Faces: Iterable[RevFaceRef]) -> None:
    Externals = {Value.ExternalValue for Value in Faces}
    if len(Externals) != 1:
        raise ValueError("selected revolve cut faces reference different documents")
    Reference = RequireNative(Header.FieldsValue.get("f38"), "moExtObject_c").FieldsValue.get("file")
    External = next(iter(Externals)).FieldsValue
    Shared = NativeRecord(External.get("shared"))
    Config = NativeRecord(External.get("refcfg"))
    if (
        not isinstance(Reference, NativeFileRef) or Reference.KindValue != 2
        or Shared.get("f20") != Reference.KindValue
        or RequireNative(Shared.get("h10"), "moCStringHandle_c").FieldsValue.get("f08") != Reference.NameValue
        or RequireNative(Shared.get("h18"), "moCStringHandle_c").FieldsValue.get("f08") != Reference.PathValue
        or Config.get("f10") != 0 or Config.get("f08") != Reference.ConfigValue
    ):
        raise ValueError("selected revolve cut face does not refer to its actual saved part and configuration")
