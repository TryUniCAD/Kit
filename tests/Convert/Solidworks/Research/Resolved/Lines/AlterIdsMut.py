from collections.abc import MutableMapping
from typing import cast as CastValue


# independent identity counters must remain separate even when native marker values are sparse
def AlterIdsMut(
    Points: tuple[MutableMapping[str, object], ...],
    Lines: tuple[MutableMapping[str, object], ...],
) -> None:
    for Index, RowValue in enumerate(Lines):
        Fields = CastValue(MutableMapping[str, object], RowValue["line"])
        Fields["f08"] = 17 + 7 * Index
        Fields["f0c"] = 101 + 2 * Index
    for Index, RowValue in enumerate(Points):
        CastValue(MutableMapping[str, object], RowValue["point"])["f0c"] = (
            301 + 3 * Index
        )
