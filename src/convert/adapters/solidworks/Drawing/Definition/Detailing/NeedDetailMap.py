from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# malformed index rows must fail before any native references are silently discarded
def NeedDetailMap(Value: object) -> Mapping[str, object]:
    if not isinstance(Value, Mapping):
        raise BodyUnsupported("drawing detailing index requires typed field mappings")
    return CastValue(Mapping[str, object], Value)
