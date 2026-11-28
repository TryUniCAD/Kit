from convert.adapters.solidworks.Archive.Bodies.CheckPacked import CheckPacked
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Archive.Scalars.ReadScalar import ReadScalar


# packed display emission computes counts and bytes from individually decoded native scalar values
def WritePackedMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    DataValue = ReadScopeValue(FrameValue.ScopeValue, RuleValue.NameValue)
    if type(DataValue) is not bytes or len(DataValue) % 8:
        raise ValueError(
            "native display scalar array requires complete packed binary64 values"
        )
    CountValue = len(DataValue) // 8
    _ = NormalizeCount(CountValue, "")
    CheckPacked(FrameValue.ScopeValue, FrameValue.NodeValue, RuleValue, CountValue)
    Values = tuple(
        ReadScalar(DataValue, Index * 8, "f64")[0] for Index in range(CountValue)
    )
    Buffer = FrameValue.WriterValue.OutputValue
    Buffer.extend(EncodeScalar(CountValue, "u32"))
    for Value in Values:
        Buffer.extend(EncodeScalar(Value, "f64"))
    FrameValue.ScopeValue.ValuesValue[RuleValue.CountValue] = CountValue
    UsageValue = FrameValue.WriterValue.ContextValue.UsageValue
    UsageValue.ByteFields.append(
        {
            "schema": UsageValue.SchemaPath[-1],
            "field": RuleValue.NameValue,
            "object_class": FrameValue.NodeValue.ClassValue.NameValue,
            "length_rule": "count_times_native_binary64_width",
            "element_type": "f64",
            "element_count": CountValue,
            "typed_values": Values,
            "declared_length": CountValue * 8,
            "observed_length": CountValue * 8,
            "completed": True,
        }
    )
