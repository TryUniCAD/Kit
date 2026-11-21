from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# source profile display order must survive validation without sorting or reconstruction
def NeedProfileRows(Value: object) -> Sequence[object]:
    if not isinstance(Value, (tuple, list)):
        raise BodyUnsupported("drawing profile display requires ordered rows")
    return CastValue(Sequence[object], Value)
