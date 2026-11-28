from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.LineOrigin import (
    LineOrigin,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# point references retain identity stamps and cache state without embedding recursive archive nodes in public metadata
def OriginMetadata(OriginValue: LineOrigin) -> Mapping[str, object]:
    Selected = OriginValue.SelectionValue.FieldsValue
    Wrapper = OriginValue.WrapperValue.FieldsValue
    return {
        "native_origin_feature_id": NativeNodeId(OriginValue.FeatureValue),
        "native_origin_name": ReadNativeName(OriginValue.FeatureValue),
        "native_feature_key": dict(NativeRecord(Selected.get("ff0"))),
        "native_origin_point_mark": Selected["f100"],
        "native_external_point_index": OriginValue.ExternalIndex,
        "native_point_creation_id": OriginValue.CreationId,
        "native_external_label": OriginValue.ExternalValue.FieldsValue.get("f28"),
        "native_reference_fields": {
            NameValue: Value
            for NameValue, Value in Selected.items()
            if NameValue not in ("f58", "f0f8")
        },
        "native_wrapper_fields": {
            NameValue: Value
            for NameValue, Value in Wrapper.items()
            if NameValue not in ("f58", "f60", "fb8")
        },
        "native_external_point_fields": {
            NameValue: Value
            for NameValue, Value in OriginValue.FieldsValue.items()
            if NameValue not in ("ext", "h1", "h2")
        },
        "native_backup_point": dict(
            NativeRecord(OriginValue.BackupValue.FieldsValue.get("f08"))
        ),
        "native_reference_owners": OriginValue.ReferenceOwners,
        "typed_archive_owner": OriginValue.OwnerValue,
        "origin_reference_freshness_checked": False,
    }
