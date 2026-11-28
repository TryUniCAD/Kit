from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the output array owns the actual body atom while alternate atom paths remain unqualified
def ReadOutputAtom(FeatureValue: ArchiveNode) -> ArchiveNode:
    FieldsValue = FeatureValue.FieldsValue
    if (
        FieldsValue.get("has_f528") != 1
        or FieldsValue.get("has_f530") != 0
        or FieldsValue.get("f538") is not None
    ):
        raise ValueError("named body requires the witnessed single output atom path")
    OutputValue = NativeRecord(FieldsValue.get("f528"))
    ItemsValue = OutputValue.get("items")
    if not isinstance(ItemsValue, list):
        raise ValueError("named body output array has no actual atom member")
    ItemsValue = CastValue(list[object], ItemsValue)
    if OutputValue.get("n") != 1 or len(ItemsValue) != 1:
        raise ValueError("named body output array is not the witnessed single atom")
    return RequireNative(NativeRecord(ItemsValue[0]).get("o"), "moAtom_c")
