from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# changed row topology must drive every following count dependent native branch
def WriteLengthMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    CountValue = len(ReadBodyRows(FrameValue.ScopeValue, RuleValue.CountValue))
    FrameValue.WriterValue.OutputValue.extend(
        EncodeScalar(CountValue, RuleValue.TypeValue)
    )
    FrameValue.ScopeValue.ValuesValue[RuleValue.NameValue] = CountValue
