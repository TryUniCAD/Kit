from contextlib import contextmanager as ContextManager
from collections.abc import Iterator

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# a selected local reference must restore the original flags after its nested typed fields
@ContextManager
def PatFieldMask(ContextValue: BodyContext, RuleValue: NativeField) -> Iterator[None]:
    FlagsValue = ContextValue.FlagsValue
    NameValue = RuleValue.NameValue
    if (
        FlagsValue.get("part_local_pattern") != 1
        or NameValue not in ("pattern_datum", "constraint_hinge")
        or RuleValue.MaskValue != 1
    ):
        raise BodyUnsupported("unsupported local pattern reference field context")
    PriorValue = FlagsValue.get(NameValue)
    FlagsValue[NameValue] = (PriorValue or 0) | RuleValue.MaskValue
    try:
        yield
    finally:
        if PriorValue is None:
            _ = FlagsValue.pop(NameValue)
        else:
            FlagsValue[NameValue] = PriorValue
