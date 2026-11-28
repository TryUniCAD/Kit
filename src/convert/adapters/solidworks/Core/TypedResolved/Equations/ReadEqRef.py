from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the actual local clone must select exactly the live annotation target apart from its own component reference
def ReadEqRef(
    LinkValue: NativeLink,
    Token: ArchiveNode,
    LiveHandle: ArchiveNode,
    MetresValue: float,
) -> tuple[ArchiveNode, Mapping[str, object]]:
    FieldsValue = Token.FieldsValue
    if FieldsValue.get("f78") is not None or not IsLineState(FieldsValue.get("f30")):
        raise ValueError("local equation dimension has external dependencies")
    Wrapper = RequireNative(FieldsValue.get("f80"), "moDimRefWrapper_c")
    WrapFields = Wrapper.FieldsValue
    Clone = RequireNative(WrapFields.get("f58"), LiveHandle.ClassValue.NameValue)
    CloneFields = Clone.FieldsValue
    LiveFields = LiveHandle.FieldsValue
    LocalOwner = RequireNative(CloneFields.get("f58"), "moUnitComponent_c")
    if (
        Clone is LiveHandle
        or LiveFields.get("f58") is not None
        or LocalOwner.FieldsValue.get("owner") is not LinkValue.ConfigValue.RootValue
        or LocalOwner.FieldsValue.get("has_ext") != 0
        or {
            KeyName: Value for KeyName, Value in CloneFields.items() if KeyName != "f58"
        }
        != {KeyName: Value for KeyName, Value in LiveFields.items() if KeyName != "f58"}
    ):
        raise ValueError("local equation dimension does not alias its exact live owner")
    if (
        WrapFields.get("fb0") != MetresValue
        or WrapFields.get("f60") is not None
        or WrapFields.get("f70") != LiveFields.get("f4c")
        or WrapFields.get("f0c") not in (-1, 0)
        or any(
            WrapFields.get(KeyName) != 0
            for KeyName in (
                "f68",
                "f6c",
                "has_f10",
                "has_f18",
                "f20",
                "f50",
                "f34",
                "f30",
                "f98",
            )
        )
        or any(WrapFields.get(KeyName) != -12345 for KeyName in ("f74", "f78", "f7c"))
        or WrapFields.get("f38") != -1
    ):
        raise ValueError("local equation dimension has unqualified wrapper state")
    return LocalOwner, {
        "token": NativeNodeSpan(LinkValue, Token),
        "wrapper": NativeNodeSpan(LinkValue, Wrapper),
        "cloned_handle": NativeNodeSpan(LinkValue, Clone),
        "live_handle": NativeNodeSpan(LinkValue, LiveHandle),
        "component": NativeNodeSpan(LinkValue, LocalOwner),
    }
