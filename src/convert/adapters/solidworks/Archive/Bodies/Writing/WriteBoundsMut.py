from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# only the full part context can emit bounded tagged slots with modeled object ownership
def WriteBoundsMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    SlotsValue = ReadBodyRows(FrameValue.ScopeValue, RuleValue.NameValue)
    if SlotsValue and RuleValue.ModeValue != "Tagged":
        raise BodyUnsupported(
            "populated SOLIDWORKS part bounds cache requires typed owners"
        )
    if len(SlotsValue) > 2:
        raise BodyUnsupported(
            "native part bounds cache count is outside zero through two"
        )
    OutputValue = FrameValue.WriterValue.OutputValue
    OutputValue.extend(EncodeScalar(len(SlotsValue), "i32"))
    for SlotValue in SlotsValue:
        if not isinstance(SlotValue, Mapping):
            raise BodyUnsupported(
                "SOLIDWORKS bounds cache slot requires a typed record"
            )
        FieldsValue = CastValue(Mapping[str, object], SlotValue)
        if set(FieldsValue) != {"k", "o"}:
            raise BodyUnsupported(
                "SOLIDWORKS bounds cache slot requires modeled fields"
            )
        KeyValue, NodeValue = FieldsValue["k"], FieldsValue["o"]
        if type(KeyValue) is not int or (KeyValue <= 0 and NodeValue is not None):
            raise BodyUnsupported(
                "SOLIDWORKS bounds cache slot has an inconsistent tag"
            )
        OutputValue.extend(EncodeScalar(KeyValue, "i32"))
        if KeyValue > 0:
            WriteNodeMut(FrameValue.WriterValue, NodeValue)
