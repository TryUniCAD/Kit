from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# ordered typed collections must reject malformed rows before their object references are followed
def NativeRows(RowsValue: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(RowsValue, (list, tuple)):
        raise ValueError("typed model expected an ordered record collection")
    return tuple(
        NativeRecord(ItemValue) for ItemValue in CastValue(Sequence[object], RowsValue)
    )
