from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadCacheNumMut import (
    ReadCacheNumMut,
)
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# bounded cache probes reject populated rows the full typed part owner can read
def ReadBBoxMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Cursor = FrameValue.ReaderValue.Cursor
    CountValue = ReadCacheNumMut(Cursor)
    if CountValue and RuleValue.ModeValue != "Tagged":
        raise BodyUnsupported(
            "populated SOLIDWORKS part bounds cache requires typed owners"
        )
    ItemsValue: list[dict[str, object]] = []
    for _ in range(CountValue):
        KeyValue = CastValue(int, ReadScalarMut(Cursor, "i32"))
        ItemsValue.append(
            {
                "k": KeyValue,
                "o": ReadNodeMut(FrameValue.ReaderValue) if KeyValue > 0 else None,
            }
        )
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = ItemsValue
