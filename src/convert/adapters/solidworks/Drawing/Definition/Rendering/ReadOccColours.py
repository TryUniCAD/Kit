from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Drawing.Definition.Rendering.NeedViewCount import (
    NeedViewCount,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.NeedViewRows import (
    NeedViewRows,
)
from convert.adapters.solidworks.Drawing.Definition.Rendering.OccColour import OccColour
from convert.adapters.solidworks.Drawing.Definition.Rendering.ReadOccColour import (
    ReadOccColour,
)


# native map uniqueness cannot discard or merge source occurrence colours
def ReadOccColours(FieldsValue: Mapping[str, object]) -> tuple[OccColour, ...]:
    RowsValue = tuple(
        ReadOccColour(ItemValue) for ItemValue in NeedViewRows(FieldsValue.get("ff60"))
    )
    NeedViewCount(FieldsValue, len(RowsValue))
    KeysValue = tuple(ItemValue.OccurrenceNum for ItemValue in RowsValue)
    if len(set(KeysValue)) != len(KeysValue):
        raise BodyUnsupported("drawing view state has duplicate occurrence colours")
    return RowsValue
