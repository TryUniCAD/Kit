from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeWord import NormalizeWord
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# unchanged runtime values preserve raw words while explicit edits replace their encoded value
def WriteNormalMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Value = ReadScopeValue(FrameValue.ScopeValue, RuleValue.NameValue)
    WireValue = FrameValue.ScopeValue.FieldsValue.get(
        RuleValue.NameValue + "#wire", Value
    )
    if (
        NormalizeWord(FrameValue.WriterValue.ContextValue, RuleValue, WireValue)
        != Value
    ):
        WireValue = Value
    FrameValue.WriterValue.OutputValue.extend(
        EncodeScalar(WireValue, RuleValue.TypeValue)
    )
