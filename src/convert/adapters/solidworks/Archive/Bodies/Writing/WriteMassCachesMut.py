from collections.abc import MutableMapping
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.CheckMassSlot import (
    CheckMassSlot,
)
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# counted cache slots derive their wire frame from the actual modeled rows
def WriteMassCachesMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ScopeValue = FrameValue.ScopeValue
    SlotsValue = ReadBodyRows(ScopeValue, RuleValue.NameValue)
    CountValue = len(SlotsValue)
    OutputValue = FrameValue.WriterValue.OutputValue
    if CountValue > 2:
        raise BodyUnsupported("native part cache count is outside zero through two")
    SelectorValue = ReadScopeValue(ScopeValue, RuleValue.OtherName)
    if type(SelectorValue) is not int or (CountValue < 2 and SelectorValue != 0):
        raise BodyUnsupported("SOLIDWORKS mass cache selector requires two slots")
    OutputValue.extend(EncodeScalar(CountValue, "i32"))
    for Index, SlotValue in enumerate(SlotsValue):
        if not isinstance(SlotValue, MutableMapping):
            raise BodyUnsupported("SOLIDWORKS mass cache slot requires modeled fields")
        FieldsValue = CastValue(MutableMapping[str, object], SlotValue)
        SlotScope = FieldScope(FieldsValue, ScopeValue, Index)
        CheckMassSlot(SlotScope)
        FrameValue.SchemaWriter(
            ReplaceValue(FrameValue, ScopeValue=SlotScope),
            "moMassPropCache_c.Serialize",
        )
    if CountValue == 2:
        OutputValue.extend(EncodeScalar(SelectorValue, "i32"))
