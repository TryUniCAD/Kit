from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.CheckPacked import CheckPacked
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeCount import NormalizeCount
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# display arrays expose typed binary64 elements while retaining the established research field shape
def ReadPackedMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Cursor = FrameValue.ReaderValue.Cursor
    CountValue = CastValue(int, ReadScalarMut(Cursor, "u32"))
    _ = NormalizeCount(CountValue, "")
    CheckPacked(FrameValue.ScopeValue, FrameValue.NodeValue, RuleValue, CountValue)
    Values = tuple(ReadScalarMut(Cursor, "f64") for _ in range(CountValue))
    FrameValue.ScopeValue.FieldsValue[RuleValue.CountValue] = CountValue
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = b"".join(
        EncodeScalar(Value, "f64") for Value in Values
    )
    UsageValue = FrameValue.ContextValue.UsageValue
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
