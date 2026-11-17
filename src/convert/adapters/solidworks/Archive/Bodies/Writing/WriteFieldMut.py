from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ValidateFields import ValidateFields
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteArrayMut import (
    WriteArrayMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteBooleanMut import (
    WriteBooleanMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteControlMut import (
    WriteControlMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNestedMut import (
    WriteNestedMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WritePresentMut import (
    WritePresentMut,
)
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteValueMut import (
    WriteValueMut,
)


# each emitted field follows declared grammar without an opaque or recorded operation fallback
def WriteFieldMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    match RuleValue.KindValue:
        case "Scalar" | "Text" | "Node":
            WriteValueMut(FrameValue, RuleValue)
        case "Base" | "Embed":
            WriteNestedMut(FrameValue, RuleValue)
        case "Array":
            WriteArrayMut(FrameValue, RuleValue)
        case "Boolean":
            WriteBooleanMut(FrameValue, RuleValue)
        case "Present":
            WritePresentMut(FrameValue, RuleValue)
        case "Branch" | "Context" | "Mask" | "Virtual":
            WriteControlMut(FrameValue, RuleValue)
        case "Validate":
            ValidateFields(
                FrameValue.WriterValue.ContextValue,
                FrameValue.ScopeValue,
                FrameValue.NodeValue,
                RuleValue.NameValue,
            )
        case "Fail":
            raise BodyUnsupported(
                f"unsupported SOLIDWORKS native field path {RuleValue.NameValue}"
            )
