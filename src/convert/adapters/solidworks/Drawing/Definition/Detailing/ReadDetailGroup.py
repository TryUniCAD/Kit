from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Drawing.Definition.Detailing.DetailGroup import (
    DetailGroup,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailMap import (
    NeedDetailMap,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailRows import (
    NeedDetailRows,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailText import (
    NeedDetailText,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedMapCount import (
    NeedMapCount,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.ReadDetailItem import (
    ReadDetailItem,
)


# native map uniqueness must be checked without sorting or rewriting the retained source rows
def ReadDetailGroup(Value: object) -> DetailGroup:
    FieldsValue = NeedDetailMap(Value)
    RowsValue = tuple(
        ReadDetailItem(ItemValue)
        for ItemValue in NeedDetailRows(FieldsValue.get("rows"))
    )
    NeedMapCount(FieldsValue, "n", len(RowsValue))
    KeysValue = tuple(
        (ItemValue.ComponentKey, ItemValue.DownstreamId) for ItemValue in RowsValue
    )
    if len(set(KeysValue)) != len(KeysValue):
        raise BodyUnsupported("drawing detailing index has duplicate component ids")
    return DetailGroup(NeedDetailText(FieldsValue.get("file")), RowsValue)
