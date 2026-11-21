from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# incomplete view cache fields must fail before any retained state is dropped
def NeedViewMap(Value: object) -> Mapping[str, object]:
    if not isinstance(Value, Mapping):
        raise BodyUnsupported("drawing view state requires typed field mappings")
    return CastValue(Mapping[str, object], Value)
