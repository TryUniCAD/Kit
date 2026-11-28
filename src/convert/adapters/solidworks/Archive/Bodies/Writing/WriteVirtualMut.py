from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.GetVirtualRule import GetVirtualRule
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame


# inherited bodies must dispatch through the concrete native owner in both directions
def WriteVirtualMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    if RuleValue.ModeValue not in ("", "Flag"):
        raise BodyUnsupported("unsupported native body virtual dispatch mode")
    TargetValue = GetVirtualRule(
        FrameValue.WriterValue.ContextValue, FrameValue.NodeValue, RuleValue
    )
    if RuleValue.ModeValue == "Flag":
        if type(TargetValue) is not bool:
            raise BodyUnsupported("native body virtual flag requires a boolean target")
        if TargetValue:
            FrameValue.FieldsWriter(FrameValue, RuleValue.BodyValue)
    elif isinstance(TargetValue, str):
        FrameValue.SchemaWriter(FrameValue, TargetValue)
    elif TargetValue is not None:
        raise BodyUnsupported("native body dispatch target is not a schema")
