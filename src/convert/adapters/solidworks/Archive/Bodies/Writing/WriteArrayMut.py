from collections.abc import MutableMapping
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteCountMut import (
    WriteCountMut,
)


# ordered row fields must remain modeled mappings rather than recorded byte operations
def WriteArrayMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ItemsValue = ReadBodyRows(FrameValue.ScopeValue, RuleValue.NameValue)
    if RuleValue.KindValue == "Repeat":
        LengthValue = ReadScopeValue(FrameValue.ScopeValue, RuleValue.CountValue)
        if type(LengthValue) is not int or NormalizeCount(
            LengthValue, RuleValue.ModeValue
        ) != len(ItemsValue):
            raise ValueError("native repeat count differs from its modeled rows")
    else:
        WriteCountMut(FrameValue, RuleValue, len(ItemsValue))
    for Index, Fields in enumerate(ItemsValue):
        if not isinstance(Fields, MutableMapping):
            raise ValueError("SOLIDWORKS body array rows require field mappings")
        ScopeValue = FieldScope(
            CastValue(MutableMapping[str, object], Fields), FrameValue.ScopeValue, Index
        )
        ChildFrame = ReplaceValue(FrameValue, ScopeValue=ScopeValue)
        FrameValue.FieldsWriter(ChildFrame, RuleValue.BodyValue)
