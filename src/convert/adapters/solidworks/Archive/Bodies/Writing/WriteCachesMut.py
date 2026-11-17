from collections.abc import MutableMapping
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# native part caches serialize modeled records rather than replaying cached payload bytes
def WriteCachesMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ItemsValue = ReadBodyRows(FrameValue.ScopeValue, RuleValue.NameValue)
    if len(ItemsValue) > 2:
        raise ValueError("native part cache count exceeds two")
    Buffer = FrameValue.WriterValue.OutputValue
    Buffer.extend(EncodeScalar(len(ItemsValue), "i32"))
    for Index, Value in enumerate(ItemsValue):
        if not isinstance(Value, MutableMapping):
            raise ValueError("native part caches require typed record mappings")
        Fields = CastValue(MutableMapping[str, object], Value)
        if RuleValue.KindValue == "MassCaches":
            ChildScope = FieldScope(Fields, FrameValue.ScopeValue, Index)
            FrameValue.SchemaWriter(
                ReplaceValue(FrameValue, ScopeValue=ChildScope),
                "moMassPropCache_c.Serialize",
            )
        else:
            KeyValue = CastValue(int, Fields["k"])
            Buffer.extend(EncodeScalar(KeyValue, "i32"))
            if KeyValue > 0:
                WriteNodeMut(FrameValue.WriterValue, Fields["o"])
    if RuleValue.KindValue == "MassCaches" and len(ItemsValue) > 1:
        Buffer.extend(
            EncodeScalar(
                ReadScopeValue(FrameValue.ScopeValue, RuleValue.OtherName), "i32"
            )
        )
