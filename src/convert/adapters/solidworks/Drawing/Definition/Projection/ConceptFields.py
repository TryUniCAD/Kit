from collections.abc import Mapping
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the concept graph must expose a framed field owner before selecting its values
def NeedConceptMap(Value: object) -> Mapping[str, object]:
    if not isinstance(Value, Mapping):
        raise ValueError("SOLIDWORKS drawing concept has an incomplete embedded record")
    return CastValue(Mapping[str, object], Value)


# validating target owners keeps class aliases from bypassing the drawing profile
def NeedConceptNode(Value: object, ClassName: str | None = None) -> ArchiveNode:
    if not isinstance(Value, ArchiveNode) or (
        ClassName is not None and Value.ClassValue.NameValue != ClassName
    ):
        raise ValueError("SOLIDWORKS drawing concept has an invalid object reference")
    return Value


# drawing transforms near the paper boundary must have finite native dimensions
def NeedDrawNumber(Value: object) -> float:
    if (
        not isinstance(Value, (float, int))
        or isinstance(Value, bool)
        or not IsFinite(Value)
    ):
        raise ValueError("SOLIDWORKS drawing concept requires a finite scalar")
    return float(Value)
