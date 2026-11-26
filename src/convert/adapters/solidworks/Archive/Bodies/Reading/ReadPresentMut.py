from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# presence flags belong to their native scalar field even when the optional record is absent
def ReadPresentMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Value = ReadScalarMut(FrameValue.ReaderValue.Cursor, RuleValue.TypeValue)
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = Value
    if Value != 0:
        FrameValue.FieldsReader(FrameValue, RuleValue.BodyValue)
