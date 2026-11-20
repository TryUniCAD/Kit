from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadLocalExpl import (
    ReadLocalExpl,
)


# a nameless exploded keyword can only stand for the actual independent configuration helper
def HasBoundExpl(LinkValue: NativeLink, RowsValue: tuple[NativeFeature, ...]) -> bool:
    if len(RowsValue) != 1:
        return False
    (RowValue,) = RowsValue
    OwnerValue = ReadLocalExpl(LinkValue)
    return (
        OwnerValue is not None
        and RowValue.object_id == NativeNodeId(OwnerValue)
        and RowValue.xml_tag == "Feature"
        and RowValue.properties.get("Name") == ""
        and not RowValue.dimensions
    )
