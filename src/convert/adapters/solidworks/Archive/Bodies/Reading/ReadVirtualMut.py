from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.GetVirtualRule import GetVirtualRule
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame


# inherited feature fields need the concrete owner to select the native virtual target
def ReadVirtualMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    TargetValue = GetVirtualRule(
        FrameValue.ContextValue, FrameValue.NodeValue, RuleValue
    )
    if RuleValue.ModeValue == "Flag":
        if TargetValue:
            FrameValue.FieldsReader(FrameValue, RuleValue.BodyValue)
        return
    if RuleValue.ModeValue:
        raise BodyUnsupported("unsupported native body virtual dispatch mode")
    if isinstance(TargetValue, str):
        FrameValue.SchemaReader(FrameValue, TargetValue)
    elif TargetValue is not None:
        raise BodyUnsupported("native body dispatch target is not a schema")
