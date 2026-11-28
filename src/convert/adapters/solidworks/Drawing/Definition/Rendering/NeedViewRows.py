from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# native colour row order must survive inspection without sorting or inferred values
def NeedViewRows(Value: object) -> Sequence[object]:
    if not isinstance(Value, (tuple, list)):
        raise BodyUnsupported("drawing view state requires ordered colour rows")
    return CastValue(Sequence[object], Value)
