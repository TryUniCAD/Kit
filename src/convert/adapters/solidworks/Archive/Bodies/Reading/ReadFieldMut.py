from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadArrayMut import ReadArrayMut
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadBooleanMut import (
    ReadBooleanMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadControlMut import (
    ReadControlMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadNestedMut import (
    ReadNestedMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadPresentMut import (
    ReadPresentMut,
)
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadValueMut import ReadValueMut
from convert.adapters.solidworks.Archive.Bodies.ValidateFields import ValidateFields


# every admitted field operation needs a concrete implementation and an explicit unsupported outcome
def ReadFieldMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    match RuleValue.KindValue:
        case "Scalar" | "Text" | "Node":
            ReadValueMut(FrameValue, RuleValue)
        case "Base" | "Embed":
            ReadNestedMut(FrameValue, RuleValue)
        case "Array":
            ReadArrayMut(FrameValue, RuleValue)
        case "Boolean":
            ReadBooleanMut(FrameValue, RuleValue)
        case "Present":
            ReadPresentMut(FrameValue, RuleValue)
        case "Branch" | "Context" | "Mask" | "Virtual":
            ReadControlMut(FrameValue, RuleValue)
        case "Validate":
            ValidateFields(
                FrameValue.ContextValue,
                FrameValue.ScopeValue,
                FrameValue.NodeValue,
                RuleValue.NameValue,
            )
        case "Fail":
            raise BodyUnsupported(
                f"unsupported SOLIDWORKS native field path {RuleValue.NameValue}"
            )
