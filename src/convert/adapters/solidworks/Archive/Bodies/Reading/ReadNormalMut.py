from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# the native runtime clears this field while typed inspection retains the original wire word
def ReadNormalMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    if RuleValue.ModeValue != "Zero":
        raise BodyUnsupported("unsupported native normalization rule")
    Value = ReadScalarMut(FrameValue.ReaderValue.Cursor, RuleValue.TypeValue)
    Fields = FrameValue.ScopeValue.FieldsValue
    Fields[RuleValue.NameValue + "#wire"] = Value
    Fields[RuleValue.NameValue] = 0
