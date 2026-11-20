from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeWord import NormalizeWord
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# normalized runtime values need their independently persisted words for archive inspection
def ReadNormalMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    ModeValue = RuleValue.ModeValue
    if ModeValue not in ("Zero", "AtomState", "AtLeast", "Identity"):
        raise BodyUnsupported("unsupported native normalization rule")
    if ModeValue in ("AtLeast", "Identity") and RuleValue.TypeValue != "i32":
        raise BodyUnsupported("native signed normalization requires an i32 word")
    Value = ReadScalarMut(FrameValue.ReaderValue.Cursor, RuleValue.TypeValue)
    Normalized = NormalizeWord(FrameValue.ContextValue, RuleValue, Value)
    Fields = FrameValue.ScopeValue.FieldsValue
    Fields[RuleValue.NameValue + "#wire"] = Value
    Fields[RuleValue.NameValue] = Normalized
