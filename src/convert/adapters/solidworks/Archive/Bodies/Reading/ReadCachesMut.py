from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# the part cache grammar has a bounded number of fully typed entries and no residual body span
def ReadCachesMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Cursor = FrameValue.ReaderValue.Cursor
    CountValue = CastValue(int, ReadScalarMut(Cursor, "i32"))
    if not 0 <= CountValue <= 2:
        raise ValueError("native part cache count is outside zero through two")
    ItemsValue: list[dict[str, object]] = []
    for Index in range(CountValue):
        Fields: dict[str, object] = {}
        if RuleValue.KindValue == "MassCaches":
            ChildScope = FieldScope(Fields, FrameValue.ScopeValue, Index)
            FrameValue.SchemaReader(
                ReplaceValue(FrameValue, ScopeValue=ChildScope),
                "moMassPropCache_c.Serialize",
            )
        else:
            KeyValue = CastValue(int, ReadScalarMut(Cursor, "i32"))
            Fields.update(
                k=KeyValue,
                o=ReadNodeMut(FrameValue.ReaderValue) if KeyValue > 0 else None,
            )
        ItemsValue.append(Fields)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = ItemsValue
    if RuleValue.KindValue == "MassCaches":
        FrameValue.ScopeValue.FieldsValue[RuleValue.OtherName] = (
            ReadScalarMut(Cursor, "i32") if CountValue > 1 else 0
        )
