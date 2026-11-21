from collections.abc import Sequence
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# native collections must stay ordered and explicit before their owners can be reconstructed
def ReadRecordRows(Value: object) -> tuple[object, ...]:
    if not isinstance(Value, (tuple, list)):
        raise BodyUnsupported("blank owner is not a typed sequence")
    return tuple(CastValue(Sequence[object], Value))
