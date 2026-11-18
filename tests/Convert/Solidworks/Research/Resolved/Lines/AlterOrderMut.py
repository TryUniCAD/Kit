from collections.abc import MutableMapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# stored row permutations must change adjacency indices without changing actual geometry or permanent native identities
def AlterOrderMut(
    Points: tuple[MutableMapping[str, object], ...],
    Lines: tuple[MutableMapping[str, object], ...],
    FieldsValue: MutableMapping[str, object],
) -> None:
    OrderValue = (2, 0, 5, 1, 4, 3)
    if len(Lines) != len(OrderValue):
        raise ValueError("line permutation requires the six sided case")
    FieldsValue["lines"] = tuple(Lines[Index] for Index in OrderValue)
    for RowValue in Points:
        for KeyValue in ("h1", "h2"):
            Handle = CastValue(
                ArchiveNode,
                CastValue(MutableMapping[str, object], RowValue["point"])[KeyValue],
            )
            Handle.FieldsValue["idx"] = OrderValue.index(
                CastValue(int, Handle.FieldsValue["idx"])
            )
