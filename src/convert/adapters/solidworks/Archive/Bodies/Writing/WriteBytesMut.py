from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# modeled fixed byte fields require exact native width and cannot absorb unknown stream content
def WriteBytesMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Value = ReadScopeValue(FrameValue.ScopeValue, RuleValue.NameValue)
    if (
        type(Value) is not bytes
        or RuleValue.MaskValue != 16
        or len(Value) != RuleValue.MaskValue
    ):
        raise ValueError(
            "native fixed byte field requires exactly sixteen modeled bytes"
        )
    FrameValue.WriterValue.OutputValue.extend(Value)
    UsageValue = FrameValue.WriterValue.ContextValue.UsageValue
    UsageValue.ByteFields.append(
        {
            "schema": UsageValue.SchemaPath[-1],
            "field": RuleValue.NameValue,
            "object_class": FrameValue.NodeValue.ClassValue.NameValue,
            "length_rule": "fixed_native_field",
            "declared_length": RuleValue.MaskValue,
            "observed_length": len(Value),
            "completed": True,
        }
    )
