from collections.abc import Mapping

from convert.adapters.solidworks.Assembly.Assembly import NativeAsmItem
from convert.adapters.solidworks.Assembly.NestedIndex.CheckIndexReference import (
    CheckIndexReference,
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
    Body = RequireRecord(Owner.RootValue.FieldsValue.get("f68"))
    Frame = RequireRecord(Body.get("list"))
    Rows = ReadRows(Frame.get("items"))
    ByFeature = {Value.feature_id: Value for Value in Items}
    if len(Rows) != len(ByFeature) or len(Items) != len(ByFeature):
        raise ValueError("nested index has an incomplete owner-local occurrence list")
    Orders: dict[int, int] = {}
    for Order, Row in enumerate(Rows):
        Reference = RequireNode(Row.get("o"), "moReference_c")
        ItemValue = ByFeature.pop(FieldInt(Reference.FieldsValue, "f08"))
        CheckIndexReference(ItemValue, Reference, Models[ItemValue.definition_id])
        Orders[ItemValue.object_id] = Order
    return Orders
