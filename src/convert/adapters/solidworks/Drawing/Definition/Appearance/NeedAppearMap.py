from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# embedded appearance owners must retain their actual typed field mappings
def NeedAppearMap(Value: object) -> Mapping[str, object]:
    if not isinstance(Value, Mapping):
        raise BodyUnsupported("drawing appearance state requires an embedded mapping")
    return CastValue(Mapping[str, object], Value)
