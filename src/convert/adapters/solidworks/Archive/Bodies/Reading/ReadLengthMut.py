from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# native length fields retain their own scalar identity even when no rows follow
def ReadLengthMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Value = ReadScalarMut(FrameValue.ReaderValue.Cursor, RuleValue.TypeValue)
    Fields = FrameValue.ScopeValue.FieldsValue
    Fields[RuleValue.NameValue] = Value
    if Value == 0:
        Fields[RuleValue.CountValue] = []
