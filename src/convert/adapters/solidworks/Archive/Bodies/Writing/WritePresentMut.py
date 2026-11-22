from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# optional field presence derives from modeled membership unless a retained flag explicitly owns it
def WritePresentMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Fields = FrameValue.ScopeValue.FieldsValue
    Value = Fields.get(RuleValue.NameValue, int(RuleValue.CountValue in Fields))
    if RuleValue.ModeValue == "ObjectPresence":
        HasObject = Fields.get(RuleValue.CountValue) is not None
        Value = Fields.get(RuleValue.NameValue, int(HasObject))
        if Value == 0 and HasObject:
            Value = 1
        if Value != 0 and RuleValue.CountValue not in Fields:
            raise ValueError("native object presence requires its modeled field")
    FrameValue.WriterValue.OutputValue.extend(EncodeScalar(Value, RuleValue.TypeValue))
    if Value != 0:
        FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
