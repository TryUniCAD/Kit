from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.EncodeCountForm import (
    EncodeCountForm,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.SelectCountWord import (
    SelectCountWord,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSplitMut import (
    WriteSplitMut,
)
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# item counts derive from the graph while equivalent signed source words remain lossless
def WriteCountMut(
    FrameValue: WriteFrame, RuleValue: NativeField, ItemCount: int
) -> None:
    _ = NormalizeCount(ItemCount, "")
    Fields = FrameValue.ScopeValue.FieldsValue
    CountName = RuleValue.CountValue or RuleValue.NameValue + "#count"
    WidthName = CountName + "#width"
    IsArchive = RuleValue.TypeValue in ("Count", "Framework")
    if not IsArchive and WidthName in Fields:
        raise ValueError("archive count width requires a vendor or framework count")
    if RuleValue.TypeValue == "Split":
        WriteSplitMut(FrameValue, RuleValue, CountName, ItemCount)
        return
    WireValue = Fields.get(CountName)
    CountValue = SelectCountWord(WireValue, ItemCount, RuleValue.ModeValue)
    if IsArchive:
        IsFramework = RuleValue.TypeValue == "Framework"
        Payload = EncodeCount(CountValue, IsFramework=IsFramework)
        if WidthName in Fields:
            Retained = EncodeCountForm(
                WireValue, Fields[WidthName], IsFramework=IsFramework
            )
            if WireValue == CountValue:
                Payload = Retained
    else:
        Payload = EncodeScalar(CountValue, RuleValue.TypeValue)
    FrameValue.WriterValue.OutputValue.extend(Payload)
    Values = FrameValue.ScopeValue.ValuesValue
    Values[CountName] = CountValue
    if IsArchive:
        Values[WidthName] = len(Payload)
