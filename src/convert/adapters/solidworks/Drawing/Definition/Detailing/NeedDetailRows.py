from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# exact row order and repeated object aliases must survive native index inspection
def NeedDetailRows(Value: object) -> Sequence[object]:
    if not isinstance(Value, (tuple, list)):
        raise BodyUnsupported("drawing detailing index requires ordered rows")
    return CastValue(Sequence[object], Value)
