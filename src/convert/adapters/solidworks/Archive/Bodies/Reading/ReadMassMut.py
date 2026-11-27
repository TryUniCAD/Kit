from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadCacheNumMut import (
    ReadCacheNumMut,
)
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut

from convert.adapters.solidworks.Archive.Bodies.Fields.CacheCountField import (
    KMassSelectorSlots,
)


# direct mass cache slots share the parent cursor and own a selector only after two slots
def ReadMassMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Cursor = FrameValue.ReaderValue.Cursor
    CountValue = ReadCacheNumMut(Cursor)
    ItemsValue: list[dict[str, object]] = []
    for Index in range(CountValue):
        Fields: dict[str, object] = {}
        ChildScope = FieldScope(Fields, FrameValue.ScopeValue, Index)
        FrameValue.SchemaReader(
            ReplaceValue(FrameValue, ScopeValue=ChildScope),
            "moMassPropCache_c.Serialize",
        )
        ItemsValue.append(Fields)
    TailValue = ReadScalarMut(Cursor, "i32") if CountValue == KMassSelectorSlots else 0
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = ItemsValue
    FrameValue.ScopeValue.FieldsValue[RuleValue.OtherName] = TailValue
