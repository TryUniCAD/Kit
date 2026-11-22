from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.SelectCountWord import (
    SelectCountWord,
)
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# the row count owns length while equivalent signed wire values remain available for replay
def WriteLengthMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    ScopeValue = FrameValue.ScopeValue
    ItemCount = NormalizeCount(len(ReadBodyRows(ScopeValue, RuleValue.CountValue)), "")
    CountValue = SelectCountWord(
        ScopeValue.FieldsValue.get(RuleValue.NameValue), ItemCount, RuleValue.ModeValue
    )
    FrameValue.WriterValue.OutputValue.extend(
        EncodeScalar(CountValue, RuleValue.TypeValue)
    )
    ScopeValue.ValuesValue[RuleValue.NameValue] = CountValue
