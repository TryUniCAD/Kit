from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# empty sketch admission must reject authored geometry instead of depending on absent optional schemas
def CheckEmptyRows(FieldsValue: Mapping[str, object]) -> None:
    Pending: list[object] = [FieldsValue]
    Visited: set[int] = set()
    while Pending:
        Current = Pending.pop()
        if id(Current) in Visited:
            continue
        Visited.add(id(Current))
        if isinstance(Current, Mapping):
            Pending.extend(CastValue(Mapping[str, object], Current).values())
        elif isinstance(Current, (list, tuple)) and Current:
            raise BodyUnsupported(
                "blank drawing Definition excludes populated sketch rows"
            )
