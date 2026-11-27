from typing import cast as CastValue
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap


# bounded receipt rows keep validation independent of any measurement resource
def ReadMeasRows(Value: object, Limit: int = 256) -> tuple[dict[str, object], ...]:
    if type(Value) is not list or len(CastValue(list[object], Value)) > Limit:
        raise ValueError("native measurement requires bounded receipt rows")
    return tuple(ReadMeasMap(ItemValue) for ItemValue in CastValue(list[object], Value))
