from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# malformed profile state must reject before native source fields can disappear
def NeedProfileMap(Value: object) -> Mapping[str, object]:
    if not isinstance(Value, Mapping):
        raise BodyUnsupported("drawing profile display requires typed field mappings")
    return CastValue(Mapping[str, object], Value)
