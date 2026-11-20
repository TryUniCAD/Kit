from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.NormalizeWord import NormalizeWord
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut


# normalized runtime values need their independently persisted words for archive inspection
def ReadNormalMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    if RuleValue.ModeValue not in ("Zero", "AtomState"):
        raise BodyUnsupported("unsupported native normalization rule")
    Value = ReadScalarMut(FrameValue.ReaderValue.Cursor, RuleValue.TypeValue)
    Normalized = NormalizeWord(FrameValue.ContextValue, RuleValue, Value)
    Fields = FrameValue.ScopeValue.FieldsValue
    Fields[RuleValue.NameValue + "#wire"] = Value
    Fields[RuleValue.NameValue] = Normalized
