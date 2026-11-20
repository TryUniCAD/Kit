from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeWord import NormalizeWord
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# a retained wire word is valid only when it represents the current runtime value
def WriteNormalMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ScopeValue = FrameValue.ScopeValue
    ContextValue = FrameValue.WriterValue.ContextValue
    Value = ReadScopeValue(ScopeValue, RuleValue.NameValue)
    WireValue = ScopeValue.FieldsValue.get(RuleValue.NameValue + "#wire", Value)
    if type(Value) is not int or type(WireValue) is not int:
        raise ValueError("native normalized value and its wire word must be integers")
    if NormalizeWord(ContextValue, RuleValue, WireValue) != Value:
        WireValue = Value
        if NormalizeWord(ContextValue, RuleValue, WireValue) != Value:
            raise ValueError(
                "native normalized value has no matching modeled wire word"
            )
    FrameValue.WriterValue.OutputValue.extend(
        EncodeScalar(WireValue, RuleValue.TypeValue)
    )
