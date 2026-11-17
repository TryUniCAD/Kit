from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# unchanged normalized booleans preserve their wire words while authored edits remain effective
def WriteBooleanMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Value = ReadScopeValue(FrameValue.ScopeValue, RuleValue.NameValue)
    Fields = FrameValue.ScopeValue.FieldsValue
    WireValue = Fields.get(RuleValue.NameValue + "#wire", Value)
    if int(WireValue != 0) != Value:
        WireValue = Value
    FrameValue.WriterValue.OutputValue.extend(
        EncodeScalar(WireValue, RuleValue.TypeValue)
    )
