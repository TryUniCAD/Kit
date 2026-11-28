from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut

from convert.adapters.solidworks.Archive.Bodies.Fields.BooleanField import (
    NormalizeFlag,
)


# native boolean normalization must never discard the original persisted scalar word
def ReadBooleanMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Value = ReadScalarMut(FrameValue.ReaderValue.Cursor, RuleValue.TypeValue)
    Fields = FrameValue.ScopeValue.FieldsValue
    Fields[RuleValue.NameValue + "#wire"] = Value
    Fields[RuleValue.NameValue] = NormalizeFlag(Value)
