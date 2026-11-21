from collections.abc import Mapping

from convert.adapters.solidworks.Assembly.Assembly import NativeAsmItem
from convert.adapters.solidworks.Assembly.NestedIndex.CheckIndexRef import (
    CheckIndexRef,
)
from convert.adapters.solidworks.Assembly.NestedIndex.IndexModel import IndexModel
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)


# the containing assembly supplies local order only after binding every indexed placement to its actual feature
def ReadIndexOrders(
    Owner: IndexModel,
    Items: tuple[NativeAsmItem, ...],
    Models: Mapping[int, IndexModel],
) -> dict[int, int]:
    if Owner.KeyValue[2] == 2:
        if Items:
            raise ValueError("nested index assigned occurrences to a part")
        return {}
    BodyValue = RequireRecord(Owner.RootValue.FieldsValue.get("f68"))
    Frame = RequireRecord(BodyValue.get("list"))
    RowsValue = ReadRows(Frame.get("items"))
    ByFeature = {Value.feature_id: Value for Value in Items}
    if len(RowsValue) != len(ByFeature) or len(Items) != len(ByFeature):
        raise ValueError("nested index has an incomplete owner-local occurrence list")
    Orders: dict[int, int] = {}
    for Order, RowValue in enumerate(RowsValue):
        Reference = RequireNode(RowValue.get("o"), "moReference_c")
        ItemValue = ByFeature.pop(FieldInt(Reference.FieldsValue, "f08"))
        CheckIndexRef(ItemValue, Reference, Models[ItemValue.definition_id])
        Orders[ItemValue.object_id] = Order
    return Orders
