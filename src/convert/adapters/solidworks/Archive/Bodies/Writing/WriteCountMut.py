from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# item counts derive from the graph while equivalent signed source words remain lossless
def WriteCountMut(
    FrameValue: WriteFrame, RuleValue: NativeField, ItemCount: int
) -> None:
    _ = NormalizeCount(ItemCount, "")
    Fields = FrameValue.ScopeValue.FieldsValue
    CountName = RuleValue.CountValue or RuleValue.NameValue + "#count"
    Buffer = FrameValue.WriterValue.OutputValue
    if RuleValue.TypeValue == "Split":
        FrameValue.ScopeValue.ValuesValue[CountName] = (
            ItemCount if RuleValue.ModeValue == "Combined" else ItemCount >> 32
        )
        if RuleValue.ModeValue != "Combined":
            FrameValue.ScopeValue.ValuesValue[RuleValue.OtherName] = (
                ItemCount & 0xFFFFFFFF
            )
        Buffer.extend(EncodeScalar(ItemCount >> 32, "u32"))
        Buffer.extend(EncodeScalar(ItemCount & 0xFFFFFFFF, "u32"))
        return
    WireValue = CastValue(int, Fields.get(CountName, ItemCount))
    CountValue = (
        WireValue
        if NormalizeCount(WireValue, RuleValue.ModeValue) == ItemCount
        else ItemCount
    )
    FrameValue.ScopeValue.ValuesValue[CountName] = CountValue
    if RuleValue.TypeValue in ("Count", "Framework"):
        Buffer.extend(
            EncodeCount(CountValue, IsFramework=RuleValue.TypeValue == "Framework")
        )
    else:
        Buffer.extend(EncodeScalar(CountValue, RuleValue.TypeValue))
