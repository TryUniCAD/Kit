from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# explicit native fixed width fields need bounded ownership rather than a residual byte tail
def ReadBytesMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    if RuleValue.MaskValue != 16:
        raise ValueError("unsupported native fixed byte field width")
    Value = FrameValue.ReaderValue.Cursor.TakeBytes(RuleValue.MaskValue)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = Value
    UsageValue = FrameValue.ContextValue.UsageValue
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
