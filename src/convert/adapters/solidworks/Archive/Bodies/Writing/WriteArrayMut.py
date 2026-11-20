from collections.abc import MutableMapping, Sequence
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteCountMut import (
    WriteCountMut,
)


# ordered row fields must remain modeled mappings rather than recorded byte operations
def WriteArrayMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Value = ReadScopeValue(FrameValue.ScopeValue, RuleValue.NameValue)
    if not isinstance(Value, Sequence) or isinstance(Value, (str, bytes, bytearray)):
        raise ValueError(
            f"SOLIDWORKS body array {RuleValue.NameValue} requires ordered rows"
        )
    ItemsValue = CastValue(Sequence[object], Value)
    WriteCountMut(FrameValue, RuleValue, len(ItemsValue))
    for Index, Fields in enumerate(ItemsValue):
        if not isinstance(Fields, MutableMapping):
            raise ValueError("SOLIDWORKS body array rows require field mappings")
        ScopeValue = FieldScope(
            CastValue(MutableMapping[str, object], Fields), FrameValue.ScopeValue, Index
        )
        ChildFrame = ReplaceValue(FrameValue, ScopeValue=ScopeValue)
        FrameValue.FieldsWriter(ChildFrame, RuleValue.BodyValue)
