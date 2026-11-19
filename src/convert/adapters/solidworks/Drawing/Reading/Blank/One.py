from collections.abc import Sequence
from typing import TypeVar
from convert.adapters.solidworks.Drawing.Reading.Blank.Require import Require

# singleton ownership must preserve the concrete value type for each native metadata caller
KValueType = TypeVar("KValueType")


# fresh blank provenance requires one actual owner rather than a preferred member of several
def One(Values: Sequence[KValueType]) -> KValueType:
    Require(len(Values) == 1, "blank owner must have exactly one member")
    return Values[0]
