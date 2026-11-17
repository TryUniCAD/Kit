from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# optional field presence derives from modeled membership unless a retained flag explicitly owns it
def WritePresentMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Fields = FrameValue.ScopeValue.FieldsValue
    Value = Fields.get(RuleValue.NameValue, int(RuleValue.CountValue in Fields))
    FrameValue.WriterValue.OutputValue.extend(EncodeScalar(Value, RuleValue.TypeValue))
    if Value != 0:
        FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
