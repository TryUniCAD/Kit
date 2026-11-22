from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# document handles can encode the unsaved path as empty on all three actual file owners
def ReadFilletKeys(FileValue: ArchiveNode) -> tuple[str, str, str, int]:
    Fields = FileValue.FieldsValue
    Shared = NativeRecord(Fields.get("shared"))
    ConfigValue = NativeRecord(Fields.get("refcfg"))
    Title, PathValue = tuple(
        ReadFilletText(
            NativeRecord(
                RequireNative(Shared.get(KeyValue), "moCStringHandle_c").FieldsValue
            )
        )
        for KeyValue in ("h10", "h18")
    )
    NameValue = ReadFilletText({"f08": ConfigValue.get("f08")})
    ConfigId = ConfigValue.get("f10")
    if not Title or NameValue != "Default" or type(ConfigId) is not int:
        raise ValueError(
            "saved fillet historical file has alternate name or configuration"
        )
    return Title, PathValue, NameValue, ConfigId


# cached and linked header codecs give their strings different field wrappers
def ReadFilletText(Fields: Mapping[str, object]) -> str:
    Value = Fields.get("f08", Fields.get("value"))
    if isinstance(Value, CStringValue):
        return Value.TextValue
    if type(Value) is str:
        return Value
    raise ValueError("saved fillet historical file lacks its actual string")
