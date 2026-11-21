from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# the model row count owns the length prefix and subsequent repeat
def WriteLengthMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ScopeValue = FrameValue.ScopeValue
    CountValue = NormalizeCount(len(ReadBodyRows(ScopeValue, RuleValue.CountValue)), "")
    FrameValue.WriterValue.OutputValue.extend(
        EncodeScalar(CountValue, RuleValue.TypeValue)
    )
    ScopeValue.ValuesValue[RuleValue.NameValue] = CountValue
