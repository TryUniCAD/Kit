from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.SystemState import (
    ReadSystemState,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# direct configuration managers are identified by typed owner fields rather than feature captions or negative ids alone
def ReadConfigHelp(LinkValue: NativeLink) -> tuple[Mapping[str, object], ...]:
    ResultValue: list[Mapping[str, object]] = []
    for FieldName, ClassName, KindValue in (
        ("f1018", "moSheetMetalMaster_c", "Sheet-Metal Master"),
        ("f13f8", "moPrtExplViewManager_c", "Exploded Views"),
    ):
        FieldValue = LinkValue.ConfigValue.RootValue.FieldsValue.get(FieldName)
        if FieldValue is None:
            continue
        NodeValue = RequireNative(FieldValue, ClassName)
        if ReadChildren(NodeValue) or NodeValue.FieldsValue.get("f18") is not None:
            raise ValueError("authored configuration manager state is not implicit")
        if FieldName == "f1018":
            if (
                NodeValue.FieldsValue.get("f08") != -1
                or NodeValue.FieldsValue.get("n370") != 0
                or NodeValue.FieldsValue.get("f358") != []
            ):
                raise ValueError("populated sheet-metal state must remain visible")
        elif (
            NodeValue.FieldsValue.get("f358") is not None
            or NodeValue.FieldsValue.get("f360") is not None
            or NodeValue.FieldsValue.get("f368") != {"n": 0, "items": []}
        ):
            raise ValueError("populated exploded-view state must remain visible")
        SpanValue = dict(NativeNodeSpan(LinkValue, NodeValue))
        SpanValue.update(
            {
                "stream": LinkValue.ConfigName,
                "owner_class": LinkValue.ConfigValue.RootValue.ClassValue.NameValue,
                "owner_object_index": LinkValue.ConfigValue.RootValue.IndexValue,
                "owner_field": FieldName,
            }
        )
        ResultValue.append(
            {
                "stored_node_id": NodeValue.FieldsValue.get("f08"),
                "class": ClassName,
                "legacy_kind": KindValue,
                "source": "direct_configuration_helper",
                "typed_archive_owner": SpanValue,
                "state": ReadSystemState(NodeValue.FieldsValue),
            }
        )
    return tuple(ResultValue)
